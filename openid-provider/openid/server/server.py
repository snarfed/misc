# -*- test-case-name: openid.test.server -*-
"""OpenID server protocol and logic.

Overview
========

    An OpenID server must perform three tasks:

        1. Examine the incoming request to determine its nature and validity.

        2. Make a decision about how to respond to this request.

        3. Format the response according to the protocol.

    The first and last of these tasks may performed by
    the L{decodeRequest<Server.decodeRequest>} and
    L{encodeResponse<Server.encodeResponse>} methods of the
    L{Server} object.  Who gets to do the intermediate task -- deciding
    how to respond to the request -- will depend on what type of request it
    is.

    If it's a request to authenticate a user (a X{C{checkid_setup}} or
    X{C{checkid_immediate}} request), you need to decide if you will assert
    that this user may claim the identity in question.  Exactly how you do
    that is a matter of application policy, but it generally involves making
    sure the user has an account with your system and is logged in, checking
    to see if that identity is hers to claim, and verifying with the user that
    she does consent to releasing that information to the party making the
    request.

    Examine the properties of the L{CheckIDRequest} object, and if
    and when you've come to a decision, form a response by calling
    L{CheckIDRequest.answer}.

    Other types of requests relate to establishing associations between client
    and server and verifying the authenticity of previous communications.
    L{Server} contains all the logic and data necessary to respond to
    such requests; just pass it to L{Server.handleRequest}.


OpenID Extensions
=================

    Do you want to provide other information for your users
    in addition to authentication?  Version 1.2 of the OpenID
    protocol allows consumers to add extensions to their requests.
    For example, with sites using the U{Simple Registration
    Extension<http://www.openidenabled.com/openid/simple-registration-extension/>},
    a user can agree to have their nickname and e-mail address sent to a
    site when they sign up.

    Since extensions do not change the way OpenID authentication works,
    code to handle extension requests may be completely separate from the
    L{OpenIDRequest} class here.  But you'll likely want data sent back by
    your extension to be signed.  L{OpenIDResponse} provides methods with
    which you can add data to it which can be signed with the other data in
    the OpenID signature.

    For example::

        # when request is a checkid_* request
        response = request.answer(True)
        # this will a signed 'openid.sreg.timezone' parameter to the response
        response.addField('sreg', 'timezone', 'America/Los_Angeles')


Stores
======

    The OpenID server needs to maintain state between requests in order
    to function.  Its mechanism for doing this is called a store.  The
    store interface is defined in C{L{openid.store.interface.OpenIDStore}}.
    Additionally, several concrete store implementations are provided, so that
    most sites won't need to implement a custom store.  For a store backed
    by flat files on disk, see C{L{openid.store.filestore.FileOpenIDStore}}.
    For stores based on MySQL or SQLite, see the C{L{openid.store.sqlstore}}
    module.


Upgrading
=========

    The keys by which a server looks up associations in its store have changed
    in version 1.2 of this library.  If your store has entries created from
    version 1.0 code, you should empty it.


@group Requests: OpenIDRequest, AssociateRequest, CheckIDRequest,
    CheckAuthRequest

@group Responses: OpenIDResponse

@group HTTP Codes: HTTP_OK, HTTP_REDIRECT, HTTP_ERROR

@group Response Encodings: ENCODE_KVFORM, ENCODE_URL
"""

import time
from copy import deepcopy

from openid import cryptutil
from openid import kvform
from openid import oidutil
from openid.dh import DiffieHellman
from openid.server.trustroot import TrustRoot
from openid.association import Association

HTTP_OK = 200
HTTP_REDIRECT = 302
HTTP_ERROR = 400

BROWSER_REQUEST_MODES = ['checkid_setup', 'checkid_immediate']
OPENID_PREFIX = 'openid.'

ENCODE_KVFORM = ('kvform',)
ENCODE_URL = ('URL/redirect',)

class OpenIDRequest(object):
    """I represent an incoming OpenID request.

    @cvar mode: the C{X{openid.mode}} of this request.
    @type mode: str
    """
    mode = None


class CheckAuthRequest(OpenIDRequest):
    """A request to verify the validity of a previous response.

    @cvar mode: "X{C{check_authentication}}"
    @type mode: str

    @ivar assoc_handle: The X{association handle} the response was signed with.
    @type assoc_handle: str
    @ivar sig: The signature to check.
    @type sig: str
    @ivar signed: The ordered list of signed items you want to check.
    @type signed: list of pairs

    @ivar invalidate_handle: An X{association handle} the client is asking
        about the validity of.  Optional, may be C{None}.
    @type invalidate_handle: str

    @see: U{OpenID Specs, Mode: check_authentication
        <http://openid.net/specs.bml#mode-check_authentication>}
    """
    mode = "check_authentication"


    def __init__(self, assoc_handle, sig, signed, invalidate_handle=None):
        """Construct me.

        These parameters are assigned directly as class attributes, see
        my L{class documentation<CheckAuthRequest>} for their descriptions.

        @type assoc_handle: str
        @type sig: str
        @type signed: list of pairs
        @type invalidate_handle: str
        """
        self.assoc_handle = assoc_handle
        self.sig = sig
        self.signed = signed
        self.invalidate_handle = invalidate_handle


    def fromQuery(klass, query):
        """Construct me from a web query.

        @param query: The query parameters as a dictionary with each
            key mapping to one value.
        @type query: dict

        @returntype: L{CheckAuthRequest}
        """
        self = klass.__new__(klass)
        try:
            self.assoc_handle = query[OPENID_PREFIX + 'assoc_handle']
            self.sig = query[OPENID_PREFIX + 'sig']
            signed_list = query[OPENID_PREFIX + 'signed']
        except KeyError, e:
            raise ProtocolError(query,
                                text="%s request missing required parameter %s"
                                " from query %s" %
                                (self.mode, e.args[0], query))

        self.invalidate_handle = query.get(OPENID_PREFIX + 'invalidate_handle')

        signed_list = signed_list.split(',')
        signed_pairs = []
        for field in signed_list:
            try:
                if field == 'mode':
                    # XXX KLUDGE HAX WEB PROTOCoL BR0KENNN
                    # openid.mode is currently check_authentication because
                    # that's the mode of this request.  But the signature
                    # was made on something with a different openid.mode.
                    # http://article.gmane.org/gmane.comp.web.openid.general/537
                    value = "id_res"
                else:
                    value = query[OPENID_PREFIX + field]
            except KeyError, e:
                raise ProtocolError(
                    query,
                    text="Couldn't find signed field %r in query %s"
                    % (field, query))
            else:
                signed_pairs.append((field, value))

        self.signed = signed_pairs
        return self

    fromQuery = classmethod(fromQuery)


    def answer(self, signatory):
        """Respond to this request.

        Given a L{Signatory}, I can check the validity of the signature and
        the X{C{invalidate_handle}}.

        @param signatory: The L{Signatory} to use to check the signature.
        @type signatory: L{Signatory}

        @returns: A response with an X{C{is_valid}} (and, if
           appropriate X{C{invalidate_handle}}) field.
        @returntype: L{OpenIDResponse}
        """
        is_valid = signatory.verify(self.assoc_handle, self.sig, self.signed)
        # Now invalidate that assoc_handle so it this checkAuth message cannot
        # be replayed.
        signatory.invalidate(self.assoc_handle, dumb=True)
        response = OpenIDResponse(self)
        response.fields['is_valid'] = (is_valid and "true") or "false"

        if self.invalidate_handle:
            assoc = signatory.getAssociation(self.invalidate_handle, dumb=False)
            if not assoc:
                response.fields['invalidate_handle'] = self.invalidate_handle
        return response


    def __str__(self):
        if self.invalidate_handle:
            ih = " invalidate? %r" % (self.invalidate_handle,)
        else:
            ih = ""
        s = "<%s handle: %r sig: %r: signed: %r%s>" % (
            self.__class__.__name__, self.assoc_handle,
            self.sig, self.signed, ih)
        return s


class PlainTextServerSession(object):
    """An object that knows how to handle association requests with no
    session type.

    @cvar session_type: The session_type for this association
        session. There is no type defined for plain-text in the OpenID
        specification, so we use 'plaintext'.
    @type session_type: str

    @see: U{OpenID Specs, Mode: associate
        <http://openid.net/specs.bml#mode-associate>}
    @see: AssociateRequest
    """
    session_type = 'plaintext'

    def fromQuery(cls, unused_request):
        return cls()

    fromQuery = classmethod(fromQuery)

    def answer(self, secret):
        return {'mac_key': oidutil.toBase64(secret)}


class DiffieHellmanServerSession(object):
    """An object that knows how to handle association requests with the
    Diffie-Hellman session type.

    @cvar session_type: The session_type for this association
        session.
    @type session_type: str

    @ivar dh: The Diffie-Hellman algorithm values for this request
    @type dh: DiffieHellman

    @ivar consumer_pubkey: The public key sent by the consumer in the
        associate request
    @type consumer_pubkey: long

    @see: U{OpenID Specs, Mode: associate
        <http://openid.net/specs.bml#mode-associate>}
    @see: AssociateRequest
    """
    session_type = 'DH-SHA1'

    def __init__(self, dh, consumer_pubkey):
        self.dh = dh
        self.consumer_pubkey = consumer_pubkey

    def fromQuery(cls, query):
        """
        @param query: The associate request's query parameters
        @type query: {str:str}

        @returntype: L{DiffieHellmanServerSession}

        @raises ProtocolError: When parameters required to establish the
            session are missing.
        """
        dh_modulus = query.get('openid.dh_modulus')
        dh_gen = query.get('openid.dh_gen')
        if (dh_modulus is None and dh_gen is not None or
            dh_gen is None and dh_modulus is not None):

            if dh_modulus is None:
                missing = 'modulus'
            else:
                missing = 'generator'

            raise ProtocolError('If non-default modulus or generator is '
                                'supplied, both must be supplied. Missing %s'
                                % (missing,))

        if dh_modulus or dh_gen:
            dh_modulus = cryptutil.base64ToLong(dh_modulus)
            dh_gen = cryptutil.base64ToLong(dh_gen)
            dh = DiffieHellman(dh_modulus, dh_gen)
        else:
            dh = DiffieHellman.fromDefaults()

        consumer_pubkey = query.get('openid.dh_consumer_public')
        if consumer_pubkey is None:
            raise ProtocolError("Public key for DH-SHA1 session "
                                "not found in query %s" % (query,))

        consumer_pubkey = cryptutil.base64ToLong(consumer_pubkey)

        return cls(dh, consumer_pubkey)

    fromQuery = classmethod(fromQuery)

    def answer(self, secret):
        mac_key = self.dh.xorSecret(self.consumer_pubkey, secret)
        return {
            'dh_server_public': cryptutil.longToBase64(self.dh.public),
            'enc_mac_key': oidutil.toBase64(mac_key),
            }


class AssociateRequest(OpenIDRequest):
    """A request to establish an X{association}.

    @cvar mode: "X{C{check_authentication}}"
    @type mode: str

    @ivar assoc_type: The type of association.  The protocol currently only
        defines one value for this, "X{C{HMAC-SHA1}}".
    @type assoc_type: str

    @ivar session: An object that knows how to handle association
        requests of a certain type.

    @see: U{OpenID Specs, Mode: associate
        <http://openid.net/specs.bml#mode-associate>}
    """

    mode = "associate"
    assoc_type = 'HMAC-SHA1'

    session_classes = {
        None: PlainTextServerSession,
        'DH-SHA1': DiffieHellmanServerSession,
        }

    def __init__(self, session):
        """Construct me.

        The session is assigned directly as a class attribute. See my
        L{class documentation<AssociateRequest>} for its description.
        """
        super(AssociateRequest, self).__init__()
        self.session = session


    def fromQuery(klass, query):
        """Construct me from a web query.

        @param query: The query parameters as a dictionary with each
            key mapping to one value.
        @type query: dict

        @returntype: L{AssociateRequest}
        """
        session_type = query.get(OPENID_PREFIX + 'session_type')
        try:
            session_class = klass.session_classes[session_type]
        except KeyError:
            raise ProtocolError(query,
                                "Unknown session type %r" % (session_type,))

        try:
            session = session_class.fromQuery(query)
        except ValueError, why:
            raise ProtocolError(query, 'Error parsing %s session: %s' %
                                (session_class.session_type, why[0]))

        return klass(session)

    fromQuery = classmethod(fromQuery)

    def answer(self, assoc):
        """Respond to this request with an X{association}.

        @param assoc: The association to send back.
        @type assoc: L{openid.association.Association}

        @returns: A response with the association information, encrypted
            to the consumer's X{public key} if appropriate.
        @returntype: L{OpenIDResponse}
        """
        response = OpenIDResponse(self)
        response.fields.update({
            'expires_in': '%d' % (assoc.getExpiresIn(),),
            'assoc_type': 'HMAC-SHA1',
            'assoc_handle': assoc.handle,
            })
        response.fields.update(self.session.answer(assoc.secret))
        if self.session.session_type != 'plaintext':
            response.fields['session_type'] = self.session.session_type

        return response


class CheckIDRequest(OpenIDRequest):
    """A request to confirm the identity of a user.

    This class handles requests for openid modes X{C{checkid_immediate}}
    and X{C{checkid_setup}}.

    @cvar mode: "X{C{checkid_immediate}}" or "X{C{checkid_setup}}"
    @type mode: str

    @ivar immediate: Is this an immediate-mode request?
    @type immediate: bool

    @ivar identity: The identity URL being checked.
    @type identity: str

    @ivar trust_root: "Are you Frank?" asks the checkid request.  "Who wants
        to know?"  C{trust_root}, that's who.  This URL identifies the party
        making the request, and the user will use that to make her decision
        about what answer she trusts them to have.
    @type trust_root: str

    @ivar return_to: The URL to send the user agent back to to reply to this
        request.
    @type return_to: str

    @ivar assoc_handle: Provided in smart mode requests, a handle for a
        previously established association.  C{None} for dumb mode requests.
    @type assoc_handle: str
    """

    def __init__(self, identity, return_to, trust_root=None, immediate=False,
                 assoc_handle=None):
        """Construct me.

        These parameters are assigned directly as class attributes, see
        my L{class documentation<CheckIDRequest>} for their descriptions.

        @raises MalformedReturnURL: When the C{return_to} URL is not a URL.
        """
        self.assoc_handle = assoc_handle
        self.identity = identity
        self.return_to = return_to
        self.trust_root = trust_root or return_to
        if immediate:
            self.immediate = True
            self.mode = "checkid_immediate"
        else:
            self.immediate = False
            self.mode = "checkid_setup"

        if not TrustRoot.parse(self.return_to):
            raise MalformedReturnURL(None, self.return_to)
        if not self.trustRootValid():
            raise UntrustedReturnURL(None, self.return_to, self.trust_root)


    def fromQuery(klass, query):
        """Construct me from a web query.

        @raises ProtocolError: When not all required parameters are present
            in the query.

        @raises MalformedReturnURL: When the C{return_to} URL is not a URL.

        @raises UntrustedReturnURL: When the C{return_to} URL is outside
            the C{trust_root}.

        @param query: The query parameters as a dictionary with each
            key mapping to one value.
        @type query: dict

        @returntype: L{CheckIDRequest}
        """
        self = klass.__new__(klass)
        mode = query[OPENID_PREFIX + 'mode']
        if mode == "checkid_immediate":
            self.immediate = True
            self.mode = "checkid_immediate"
        else:
            self.immediate = False
            self.mode = "checkid_setup"

        required = [
            'identity',
            'return_to',
            ]

        for field in required:
            value = query.get(OPENID_PREFIX + field)
            if not value:
                raise ProtocolError(
                    query,
                    text="Missing required field %s from %r"
                    % (field, query))
            setattr(self, field, value)

        # There's a case for making self.trust_root be a TrustRoot
        # here.  But if TrustRoot isn't currently part of the "public" API,
        # I'm not sure it's worth doing.
        self.trust_root = query.get(OPENID_PREFIX + 'trust_root', self.return_to)
        self.assoc_handle = query.get(OPENID_PREFIX + 'assoc_handle')

        # Using TrustRoot.parse here is a bit misleading, as we're not
        # parsing return_to as a trust root at all.  However, valid URLs
        # are valid trust roots, so we can use this to get an idea if it
        # is a valid URL.  Not all trust roots are valid return_to URLs,
        # however (particularly ones with wildcards), so this is still a
        # little sketchy.
        if not TrustRoot.parse(self.return_to):
            raise MalformedReturnURL(query, self.return_to)

        # I first thought that checking to see if the return_to is within
        # the trust_root is premature here, a logic-not-decoding thing.  But
        # it was argued that this is really part of data validation.  A
        # request with an invalid trust_root/return_to is broken regardless of
        # application, right?
        if not self.trustRootValid():
            raise UntrustedReturnURL(query, self.return_to, self.trust_root)

        return self

    fromQuery = classmethod(fromQuery)


    def trustRootValid(self):
        """Is my return_to under my trust_root?

        @returntype: bool
        """
        if not self.trust_root:
            return True
        tr = TrustRoot.parse(self.trust_root)
        if tr is None:
            raise MalformedTrustRoot(None, self.trust_root)
        return tr.validateURL(self.return_to)


    def answer(self, allow, server_url=None):
        """Respond to this request.

        @param allow: Allow this user to claim this identity, and allow the
            consumer to have this information?
        @type allow: bool

        @param server_url: When an immediate mode request does not
            succeed, it gets back a URL where the request may be
            carried out in a not-so-immediate fashion.  Pass my URL
            in here (the fully qualified address of this server's
            endpoint, i.e.  C{http://example.com/server}), and I
            will use it as a base for the URL for a new request.

            Optional for requests where C{CheckIDRequest.immediate} is C{False}
            or C{allow} is C{True}.

        @type server_url: str

        @returntype: L{OpenIDResponse}
        """
        if allow or self.immediate:
            mode = 'id_res'
        else:
            mode = 'cancel'

        response = OpenIDResponse(self)

        if allow:
            response.addFields(None, {
                'mode': mode,
                'identity': self.identity,
                'return_to': self.return_to,
                })
        else:
            response.addField(None, 'mode', mode, False)
            if self.immediate:
                if not server_url:
                    raise ValueError("setup_url is required for allow=False "
                                     "in immediate mode.")
                # Make a new request just like me, but with immediate=False.
                setup_request = self.__class__(
                    self.identity, self.return_to, self.trust_root,
                    immediate=False, assoc_handle=self.assoc_handle)
                setup_url = setup_request.encodeToURL(server_url)
                response.addField(None, 'user_setup_url', setup_url, False)

        return response


    def encodeToURL(self, server_url):
        """Encode this request as a URL to GET.

        @param server_url: The URL of the OpenID server to make this request of.
        @type server_url: str

        @returntype: str
        """
        # Imported from the alternate reality where these classes are used
        # in both the client and server code, so Requests are Encodable too.
        # That's right, code imported from alternate realities all for the
        # love of you, id_res/user_setup_url.
        q = {'mode': self.mode,
             'identity': self.identity,
             'return_to': self.return_to}
        if self.trust_root:
            q['trust_root'] = self.trust_root
        if self.assoc_handle:
            q['assoc_handle'] = self.assoc_handle

        q = dict([(OPENID_PREFIX + k, v) for k, v in q.iteritems()])

        return oidutil.appendArgs(server_url, q)


    def getCancelURL(self):
        """Get the URL to cancel this request.

        Useful for creating a "Cancel" button on a web form so that operation
        can be carried out directly without another trip through the server.

        (Except you probably want to make another trip through the server so
        that it knows that the user did make a decision.  Or you could simulate
        this method by doing C{.answer(False).encodeToURL()})

        @returntype: str
        @returns: The return_to URL with openid.mode = cancel.
        """
        if self.immediate:
            raise ValueError("Cancel is not an appropriate response to "
                             "immediate mode requests.")
        return oidutil.appendArgs(self.return_to, {OPENID_PREFIX + 'mode':
                                                   'cancel'})


    def __str__(self):
        return '<%s id:%r im:%s tr:%r ah:%r>' % (self.__class__.__name__,
                                                 self.identity,
                                                 self.immediate,
                                                 self.trust_root,
                                                 self.assoc_handle)



class OpenIDResponse(object):
    """I am a response to an OpenID request.

    @ivar request: The request I respond to.
    @type request: L{OpenIDRequest}

    @ivar fields: My parameters as a dictionary with each key mapping to
        one value.  Keys are parameter names with no leading "C{openid.}".
        e.g.  "C{identity}" and "C{mac_key}", never "C{openid.identity}".
    @type fields: dict

    @ivar signed: The names of the fields which should be signed.
    @type signed: list of str
    """

    # Implementer's note: In a more symmetric client/server
    # implementation, there would be more types of OpenIDResponse
    # object and they would have validated attributes according to the
    # type of response.  But as it is, Response objects in a server are
    # basically write-only, their only job is to go out over the wire,
    # so this is just a loose wrapper around OpenIDResponse.fields.

    def __init__(self, request):
        """Make a response to an L{OpenIDRequest}.

        @type request: L{OpenIDRequest}
        """
        self.request = request
        self.fields = {}
        self.signed = []

    def __str__(self):
        return "%s for %s: %s" % (
            self.__class__.__name__,
            self.request.__class__.__name__,
            self.fields)


    def addField(self, namespace, key, value, signed=True):
        """Add a field to this response.

        @param namespace: The extension namespace the field is in, with no
            leading "C{openid.}" e.g. "C{sreg}".
        @type namespace: str

        @param key: The field's name, e.g. "C{fullname}".
        @type key: str

        @param value: The field's value.
        @type value: str

        @param signed: Whether this field should be signed.
        @type signed: bool
        """
        if namespace:
            key = '%s.%s' % (namespace, key)
        self.fields[key] = value
        if signed and key not in self.signed:
            self.signed.append(key)


    def addFields(self, namespace, fields, signed=True):
        """Add a number of fields to this response.

        @param namespace: The extension namespace the field is in, with no
            leading "C{openid.}" e.g. "C{sreg}".
        @type namespace: str

        @param fields: A dictionary with the fields to add.
            e.g. C{{"fullname": "Frank the Goat"}}

        @param signed: Whether these fields should be signed.
        @type signed: bool
        """
        for key, value in fields.iteritems():
            self.addField(namespace, key, value, signed)


    def update(self, namespace, other):
        """Update my fields with those from another L{OpenIDResponse}.

        The idea here is that if you write an OpenID extension, it
        could produce a Response object with C{fields} and C{signed}
        attributes, and you could merge it with me using this method
        before I am signed and sent.

        All entries in C{other.fields} will have their keys prefixed
        with C{namespace} and added to my fields.  All elements of
        C{other.signed} will be prefixed with C{namespace} and added
        to my C{signed} list.

        @param namespace: The extension namespace the field is in, with no
            leading "C{openid.}" e.g. "C{sreg}".
        @type namespace: str

        @param other: A response object to update from.
        @type other: L{OpenIDResponse}
        """
        if namespace:
            namespaced_fields = dict([('%s.%s' % (namespace, k), v) for k, v
                                      in other.fields.iteritems()])
            namespaced_signed = ['%s.%s' % (namespace, k) for k
                                 in other.signed]
        else:
            namespaced_fields = other.fields
            namespaced_signed = other.signed
        self.fields.update(namespaced_fields)
        self.signed.extend(namespaced_signed)


    def needsSigning(self):
        """Does this response require signing?

        @returntype: bool
        """
        return (
            (self.request.mode in ['checkid_setup', 'checkid_immediate'])
            and self.signed
            )


    # implements IEncodable

    def whichEncoding(self):
        """How should I be encoded?

        @returns: one of ENCODE_URL or ENCODE_KVFORM.
        """
        if self.request.mode in BROWSER_REQUEST_MODES:
            return ENCODE_URL
        else:
            return ENCODE_KVFORM


    def encodeToURL(self):
        """Encode a response as a URL for the user agent to GET.

        You will generally use this URL with a HTTP redirect.

        @returns: A URL to direct the user agent back to.
        @returntype: str
        """
        fields = dict(
            [(OPENID_PREFIX + k, v.encode('UTF8')) for k, v in self.fields.iteritems()])
        return oidutil.appendArgs(self.request.return_to, fields)


    def encodeToKVForm(self):
        """Encode a response in key-value colon/newline format.

        This is a machine-readable format used to respond to messages which
        came directly from the consumer and not through the user agent.

        @see: OpenID Specs,
           U{Key-Value Colon/Newline format<http://openid.net/specs.bml#keyvalue>}

        @returntype: str
        """
        return kvform.dictToKV(self.fields)


    def __str__(self):
        return "%s for %s: signed%s %s" % (
            self.__class__.__name__,
            self.request.__class__.__name__,
            self.signed, self.fields)



class WebResponse(object):
    """I am a response to an OpenID request in terms a web server understands.

    I generally come from an L{Encoder}, either directly or from
    L{Server.encodeResponse}.

    @ivar code: The HTTP code of this response.
    @type code: int

    @ivar headers: Headers to include in this response.
    @type headers: dict

    @ivar body: The body of this response.
    @type body: str
    """

    def __init__(self, code=HTTP_OK, headers=None, body=""):
        """Construct me.

        These parameters are assigned directly as class attributes, see
        my L{class documentation<WebResponse>} for their descriptions.
        """
        self.code = code
        if headers is not None:
            self.headers = headers
        else:
            self.headers = {}
        self.body = body



class Signatory(object):
    """I sign things.

    I also check signatures.

    All my state is encapsulated in an
    L{OpenIDStore<openid.store.interface.OpenIDStore>}, which means
    I'm not generally pickleable but I am easy to reconstruct.

    @cvar SECRET_LIFETIME: The number of seconds a secret remains valid.
    @type SECRET_LIFETIME: int
    """

    SECRET_LIFETIME = 14 * 24 * 60 * 60 # 14 days, in seconds

    # keys have a bogus server URL in them because the filestore
    # really does expect that key to be a URL.  This seems a little
    # silly for the server store, since I expect there to be only one
    # server URL.
    _normal_key = 'http://localhost/|normal'
    _dumb_key = 'http://localhost/|dumb'


    def __init__(self, store):
        """Create a new Signatory.

        @param store: The back-end where my associations are stored.
        @type store: L{openid.store.interface.OpenIDStore}
        """
        assert store is not None
        self.store = store


    def verify(self, assoc_handle, sig, signed_pairs):
        """Verify that the signature for some data is valid.

        @param assoc_handle: The handle of the association used to sign the
            data.
        @type assoc_handle: str

        @param sig: The base-64 encoded signature to check.
        @type sig: str

        @param signed_pairs: The data to check, an ordered list of key-value
            pairs.  The keys should be as they are in the request's C{signed}
            list, without any C{"openid."} prefix.
        @type signed_pairs: list of pairs

        @returns: C{True} if the signature is valid, C{False} if not.
        @returntype: bool
        """
        assoc = self.getAssociation(assoc_handle, dumb=True)
        if not assoc:
            oidutil.log("failed to get assoc with handle %r to verify sig %r"
                        % (assoc_handle, sig))
            return False

        # Not using Association.checkSignature here is intentional;
        # Association should not know things like "the list of signed pairs is
        # in the request's 'signed' parameter and it is comma-separated."
        expected_sig = oidutil.toBase64(assoc.sign(signed_pairs))

        return sig == expected_sig


    def sign(self, response):
        """Sign a response.

        I take a L{OpenIDResponse}, create a signature for everything
        in its L{signed<OpenIDResponse.signed>} list, and return a new
        copy of the response object with that signature included.

        @param response: A response to sign.
        @type response: L{OpenIDResponse}

        @returns: A signed copy of the response.
        @returntype: L{OpenIDResponse}
        """
        signed_response = deepcopy(response)
        assoc_handle = response.request.assoc_handle
        if assoc_handle:
            # normal mode
            assoc = self.getAssociation(assoc_handle, dumb=False)
            if not assoc:
                # fall back to dumb mode
                signed_response.fields['invalidate_handle'] = assoc_handle
                assoc = self.createAssociation(dumb=True)
        else:
            # dumb mode.
            assoc = self.createAssociation(dumb=True)

        signed_response.fields['assoc_handle'] = assoc.handle
        assoc.addSignature(signed_response.signed, signed_response.fields,
                           prefix='')
        return signed_response


    def createAssociation(self, dumb=True, assoc_type='HMAC-SHA1'):
        """Make a new association.

        @param dumb: Is this association for a dumb-mode transaction?
        @type dumb: bool

        @param assoc_type: The type of association to create.  Currently
            there is only one type defined, C{HMAC-SHA1}.
        @type assoc_type: str

        @returns: the new association.
        @returntype: L{openid.association.Association}
        """
        secret = cryptutil.getBytes(20)
        uniq = oidutil.toBase64(cryptutil.getBytes(4))
        handle = '{%s}{%x}{%s}' % (assoc_type, int(time.time()), uniq)

        assoc = Association.fromExpiresIn(
            self.SECRET_LIFETIME, handle, secret, assoc_type)

        if dumb:
            key = self._dumb_key
        else:
            key = self._normal_key
        self.store.storeAssociation(key, assoc)
        return assoc


    def getAssociation(self, assoc_handle, dumb):
        """Get the association with the specified handle.

        @type assoc_handle: str

        @param dumb: Is this association used with dumb mode?
        @type dumb: bool

        @returns: the association, or None if no valid association with that
            handle was found.
        @returntype: L{openid.association.Association}
        """
        # Hmm.  We've created an interface that deals almost entirely with
        # assoc_handles.  The only place outside the Signatory that uses this
        # (and thus the only place that ever sees Association objects) is
        # when creating a response to an association request, as it must have
        # the association's secret.

        if assoc_handle is None:
            raise ValueError("assoc_handle must not be None")

        if dumb:
            key = self._dumb_key
        else:
            key = self._normal_key
        assoc = self.store.getAssociation(key, assoc_handle)
        if assoc is not None and assoc.expiresIn <= 0:
            oidutil.log("requested %sdumb key %r is expired (by %s seconds)" %
                        ((not dumb) and 'not-' or '',
                         assoc_handle, assoc.expiresIn))
            self.store.removeAssociation(key, assoc_handle)
            assoc = None
        return assoc


    def invalidate(self, assoc_handle, dumb):
        """Invalidates the association with the given handle.

        @type assoc_handle: str

        @param dumb: Is this association used with dumb mode?
        @type dumb: bool
        """
        if dumb:
            key = self._dumb_key
        else:
            key = self._normal_key
        self.store.removeAssociation(key, assoc_handle)



class Encoder(object):
    """I encode responses in to L{WebResponses<WebResponse>}.

    If you don't like L{WebResponses<WebResponse>}, you can do
    your own handling of L{OpenIDResponses<OpenIDResponse>} with
    L{OpenIDResponse.whichEncoding}, L{OpenIDResponse.encodeToURL}, and
    L{OpenIDResponse.encodeToKVForm}.
    """

    responseFactory = WebResponse


    def encode(self, response):
        """Encode a response to a L{WebResponse}.

        @raises EncodingError: When I can't figure out how to encode this
            message.
        """
        encode_as = response.whichEncoding()
        if encode_as == ENCODE_KVFORM:
            wr = self.responseFactory(body=response.encodeToKVForm())
            if isinstance(response, Exception):
                wr.code = HTTP_ERROR
        elif encode_as == ENCODE_URL:
            location = response.encodeToURL()
            wr = self.responseFactory(code=HTTP_REDIRECT,
                                      headers={'location': location})
        else:
            # Can't encode this to a protocol message.  You should probably
            # render it to HTML and show it to the user.
            raise EncodingError(response)
        return wr



class SigningEncoder(Encoder):
    """I encode responses in to L{WebResponses<WebResponse>}, signing them when required.
    """

    def __init__(self, signatory):
        """Create a L{SigningEncoder}.

        @param signatory: The L{Signatory} I will make signatures with.
        @type signatory: L{Signatory}
        """
        self.signatory = signatory


    def encode(self, response):
        """Encode a response to a L{WebResponse}, signing it first if appropriate.

        @raises EncodingError: When I can't figure out how to encode this
            message.

        @raises AlreadySigned: When this response is already signed.

        @returntype: L{WebResponse}
        """
        # the isinstance is a bit of a kludge... it means there isn't really
        # an adapter to make the interfaces quite match.
        if (not isinstance(response, Exception)) and response.needsSigning():
            if not self.signatory:
                raise ValueError(
                    "Must have a store to sign this request: %s" %
                    (response,), response)
            if 'sig' in response.fields:
                raise AlreadySigned(response)
            response = self.signatory.sign(response)
        return super(SigningEncoder, self).encode(response)



class Decoder(object):
    """I decode an incoming web request in to a L{OpenIDRequest}.
    """

    _handlers = {
        'checkid_setup': CheckIDRequest.fromQuery,
        'checkid_immediate': CheckIDRequest.fromQuery,
        'check_authentication': CheckAuthRequest.fromQuery,
        'associate': AssociateRequest.fromQuery,
        }


    def decode(self, query):
        """I transform query parameters into an L{OpenIDRequest}.

        If the query does not seem to be an OpenID request at all, I return
        C{None}.

        @param query: The query parameters as a dictionary with each
            key mapping to one value.
        @type query: dict

        @raises ProtocolError: When the query does not seem to be a valid
            OpenID request.

        @returntype: L{OpenIDRequest}
        """
        if not query:
            return None
        myquery = dict(filter(lambda (k, v): k.startswith(OPENID_PREFIX),
                              query.iteritems()))
        if not myquery:
            return None

        mode = myquery.get(OPENID_PREFIX + 'mode')
        if isinstance(mode, list):
            raise TypeError("query dict must have one value for each key, "
                            "not lists of values.  Query is %r" % (query,))

        if not mode:
            raise ProtocolError(
                query,
                text="No %smode value in query %r" % (
                OPENID_PREFIX, query))
        handler = self._handlers.get(mode, self.defaultDecoder)
        return handler(query)


    def defaultDecoder(self, query):
        """Called to decode queries when no handler for that mode is found.

        @raises ProtocolError: This implementation always raises
            L{ProtocolError}.
        """
        mode = query[OPENID_PREFIX + 'mode']
        raise ProtocolError(
            query,
            text="No decoder for mode %r" % (mode,))



class Server(object):
    """I handle requests for an OpenID server.

    Some types of requests (those which are not C{checkid} requests) may be
    handed to my L{handleRequest} method, and I will take care of it and
    return a response.

    For your convenience, I also provide an interface to L{Decoder.decode}
    and L{SigningEncoder.encode} through my methods L{decodeRequest} and
    L{encodeResponse}.

    All my state is encapsulated in an
    L{OpenIDStore<openid.store.interface.OpenIDStore>}, which means
    I'm not generally pickleable but I am easy to reconstruct.

    Example::

        oserver = Server(FileOpenIDStore(data_path))
        request = oserver.decodeRequest(query)
        if request.mode in ["checkid_immediate", "checkid_setup"]:
            if self.isAuthorized(request.identity, request.trust_root):
                response = request.answer(True)
            elif request.immediate:
                response = request.answer(False, self.base_url)
            else:
                self.showDecidePage(request)
                return
        else:
            response = oserver.handleRequest(request)

        webresponse = oserver.encode(response)

    @ivar signatory: I'm using this for associate requests and to sign things.
    @type signatory: L{Signatory}

    @ivar decoder: I'm using this to decode things.
    @type decoder: L{Decoder}

    @ivar encoder: I'm using this to encode things.
    @type encoder: L{Encoder}
    """

    signatoryClass = Signatory
    encoderClass = SigningEncoder
    decoderClass = Decoder

    def __init__(self, store):
        """A new L{Server}.

        @param store: The back-end where my associations are stored.
        @type store: L{openid.store.interface.OpenIDStore}
        """
        self.store = store
        self.signatory = self.signatoryClass(self.store)
        self.encoder = self.encoderClass(self.signatory)
        self.decoder = self.decoderClass()


    def handleRequest(self, request):
        """Handle a request.

        Give me a request, I will give you a response.  Unless it's a type
        of request I cannot handle myself, in which case I will raise
        C{NotImplementedError}.  In that case, you can handle it yourself,
        or add a method to me for handling that request type.

        @raises NotImplementedError: When I do not have a handler defined
            for that type of request.
        """
        handler = getattr(self, 'openid_' + request.mode, None)
        if handler is not None:
            return handler(request)
        else:
            raise NotImplementedError(
                "%s has no handler for a request of mode %r." %
                (self, request.mode))


    def openid_check_authentication(self, request):
        """Handle and respond to {check_authentication} requests.

        @returntype: L{OpenIDResponse}
        """
        return request.answer(self.signatory)


    def openid_associate(self, request):
        """Handle and respond to {associate} requests.

        @returntype: L{OpenIDResponse}
        """
        assoc = self.signatory.createAssociation(dumb=False)
        return request.answer(assoc)


    def decodeRequest(self, query):
        """Transform query parameters into an L{OpenIDRequest}.

        If the query does not seem to be an OpenID request at all, I return
        C{None}.

        @param query: The query parameters as a dictionary with each
            key mapping to one value.
        @type query: dict

        @raises ProtocolError: When the query does not seem to be a valid
            OpenID request.

        @returntype: L{OpenIDRequest}

        @see: L{Decoder.decode}
        """
        return self.decoder.decode(query)


    def encodeResponse(self, response):
        """Encode a response to a L{WebResponse}, signing it first if appropriate.

        @raises EncodingError: When I can't figure out how to encode this
            message.

        @raises AlreadySigned: When this response is already signed.

        @returntype: L{WebResponse}

        @see: L{Encoder.encode}
        """
        return self.encoder.encode(response)



class ProtocolError(Exception):
    """A message did not conform to the OpenID protocol.

    @ivar query: The query that is failing to be a valid OpenID request.
    @type query: dict
    """

    def __init__(self, query, text=None):
        """When an error occurs.

        @param query: The query that is failing to be a valid OpenID request.
        @type query: dict

        @param text: A message about the encountered error.  Set as C{args[0]}.
        @type text: str
        """
        self.query = query
        Exception.__init__(self, text)


    def hasReturnTo(self):
        """Did this request have a return_to parameter?

        @returntype: bool
        """
        if self.query is None:
            return False
        else:
            return (OPENID_PREFIX + 'return_to') in self.query


    # implements IEncodable

    def encodeToURL(self):
        """Encode a response as a URL for the user agent to GET.

        You will generally use this URL with a HTTP redirect.

        @returns: A URL to direct the user agent back to.
        @returntype: str
        """
        return_to = self.query.get(OPENID_PREFIX + 'return_to')
        if not return_to:
            raise ValueError("I have no return_to URL.")
        return oidutil.appendArgs(return_to, {
            'openid.mode': 'error',
            'openid.error': str(self),
            })


    def encodeToKVForm(self):
        """Encode a response in key-value colon/newline format.

        This is a machine-readable format used to respond to messages which
        came directly from the consumer and not through the user agent.

        @see: OpenID Specs,
           U{Key-Value Colon/Newline format<http://openid.net/specs.bml#keyvalue>}

        @returntype: str
        """
        return kvform.dictToKV({
            'mode': 'error',
            'error': str(self),
            })


    def whichEncoding(self):
        """How should I be encoded?

        @returns: one of ENCODE_URL, ENCODE_KVFORM, or None.  If None,
            I cannot be encoded as a protocol message and should be
            displayed to the user.
        """
        if self.hasReturnTo():
            return ENCODE_URL

        if self.query is None:
            return None

        mode = self.query.get('openid.mode')
        if mode:
            if mode not in BROWSER_REQUEST_MODES:
                return ENCODE_KVFORM

        # According to the OpenID spec as of this writing, we are probably
        # supposed to switch on request type here (GET versus POST) to figure
        # out if we're supposed to print machine-readable or human-readable
        # content at this point.  GET/POST seems like a pretty lousy way of
        # making the distinction though, as it's just as possible that the
        # user agent could have mistakenly been directed to post to the
        # server URL.

        # Basically, if your request was so broken that you didn't manage to
        # include an openid.mode, I'm not going to worry too much about
        # returning you something you can't parse.
        return None



class EncodingError(Exception):
    """Could not encode this as a protocol message.

    You should probably render it and show it to the user.

    @ivar response: The response that failed to encode.
    @type response: L{OpenIDResponse}
    """

    def __init__(self, response):
        Exception.__init__(self, response)
        self.response = response



class AlreadySigned(EncodingError):
    """This response is already signed."""



class UntrustedReturnURL(ProtocolError):
    """A return_to is outside the trust_root."""

    def __init__(self, query, return_to, trust_root):
        ProtocolError.__init__(self, query)
        self.return_to = return_to
        self.trust_root = trust_root

    def __str__(self):
        return "return_to %r not under trust_root %r" % (self.return_to,
                                                         self.trust_root)


class MalformedReturnURL(ProtocolError):
    """The return_to URL doesn't look like a valid URL."""
    def __init__(self, query, return_to):
        self.return_to = return_to
        ProtocolError.__init__(self, query)



class MalformedTrustRoot(ProtocolError):
    """The trust root is not well-formed.

    @see: OpenID Specs, U{openid.trust_root<http://openid.net/specs.bml#mode-checkid_immediate>}
    """
    pass


#class IEncodable: # Interface
#     def encodeToURL(return_to):
#         """Encode a response as a URL for redirection.
#
#         @returns: A URL to direct the user agent back to.
#         @returntype: str
#         """
#         pass
#
#     def encodeToKvform():
#         """Encode a response in key-value colon/newline format.
#
#         This is a machine-readable format used to respond to messages which
#         came directly from the consumer and not through the user agent.
#
#         @see: OpenID Specs,
#            U{Key-Value Colon/Newline format<http://openid.net/specs.bml#keyvalue>}
#
#         @returntype: str
#         """
#         pass
#
#     def whichEncoding():
#         """How should I be encoded?
#
#         @returns: one of ENCODE_URL, ENCODE_KVFORM, or None.  If None,
#             I cannot be encoded as a protocol message and should be
#             displayed to the user.
#         """
#         pass
