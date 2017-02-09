#!/usr/bin/python
#
# Copyright 2006 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An OpenID Provider. Allows Google users to log into OpenID servers using
their Google Account.

Part of http://code.google.com/p/google-app-engine-samples/.

For more about OpenID, see:
  http://openid.net/
  http://openid.net/about.bml

Uses JanRain's Python OpenID library, version 1.2.0, licensed under the
Apache Software License 2.0:
  http://openidenabled.com/python-openid/

It uses version 1.2.0 (included here), not a later version, because this app
was originally written a long time ago when 1.2.0 was the latest version
available. Porting to 2.1.1 or later should be straightforward.

The JanRain library includes a reference OpenID consumer that can be used to
test this provider. After starting the dev_appserver with this app, unpack the
JanRain library and run these commands from its root directory:

  setenv PYTHONPATH .
  python ./examples/consumer.py -s localhost

Then go to http://localhost:8001/ in your browser, type in
http://localhost:8080/myname as your openid identifier, and click Verify.
"""

import cgi
import Cookie
import datetime
import logging
import os
import pickle
import pprint
import sys
import traceback
import urlparse
import wsgiref.handlers

from google.appengine.api import datastore
from google.appengine.api import users
from google.appengine.ext.webapp import template
import webapp2

from openid.server import server as OpenIDServer
import store


# Set to True if stack traces should be shown in the browser, etc.
_DEBUG = False

# the global openid server instance
oidserver = OpenIDServer.Server(store.DatastoreStore())


class Handler(webapp2.RequestHandler):
  """A base handler class with a couple OpenID-specific utilities."""

  def ArgsToDict(self):
    """Converts the URL and POST parameters to a singly-valued dictionary.

    Returns:
      dict with the URL and POST body parameters
    """
    req = self.request
    return dict([(arg, req.get(arg)) for arg in req.arguments()])

  def HasCookie(self):
    """Returns True if we "remember" the user, False otherwise.

    Determines whether the user has used OpenID before and asked us to
    remember them - ie, if the user agent provided an 'openid_remembered'
    cookie.

    Returns:
      True if we remember the user, False otherwise.
    """
    cookies = os.environ.get('HTTP_COOKIE', None)
    if cookies:
      morsel = Cookie.BaseCookie(cookies).get('openid_remembered')
      if morsel and morsel.value == 'yes':
        return True

    return False

  def GetOpenIdRequest(self):
    """Creates and OpenIDRequest for this request, if appropriate.

    If this request is not an OpenID request, returns None. If an error occurs
    while parsing the arguments, returns False and shows the error page.

    Return:
      An OpenIDRequest, if this user request is an OpenID request. Otherwise
      False.
    """
    try:
      oidrequest = oidserver.decodeRequest(self.ArgsToDict())
      logging.debug('OpenID request: %s' % oidrequest)
      return oidrequest
    except:
      trace = ''.join(traceback.format_exception(*sys.exc_info()))
      self.ReportError('Error parsing OpenID request:\n%s' % trace)
      return False

  def Respond(self, oidresponse):
    """Send an OpenID response.

    Args:
      oidresponse: OpenIDResponse
      The response to send, usually created by OpenIDRequest.answer().
    """
    logging.warning('Respond: oidresponse.request.mode ' + oidresponse.request.mode)

    if oidresponse.request.mode in ['checkid_immediate', 'checkid_setup']:
      user = users.get_current_user()
      if user:
        # add nickname, using the Simple Registration Extension:
        # http://www.openidenabled.com/openid/simple-registration-extension/
        oidresponse.addField('sreg', 'nickname', user.nickname())

    logging.debug('Using response: %s' % oidresponse)
    encoded_response = oidserver.encodeResponse(oidresponse)

    # update() would be nice, but wsgiref.headers.Headers doesn't implement it
    for header, value in encoded_response.headers.items():
      self.response.headers[header] = str(value)

    if encoded_response.code in (301, 302):
      self.redirect(self.response.headers['location'])
    else:
      self.response.set_status(encoded_response.code)

    if encoded_response.body:
      logging.debug('Sending response body: %s' % encoded_response.body)
      self.response.out.write(encoded_response.body)
    else:
      self.response.out.write('')

  def Render(self, template_name, extra_values={}):
    """Render the given template, including the extra (optional) values.

    Args:
      template_name: string
      The template to render.

      extra_values: dict
      Template values to provide to the template.
    """
    parsed = urlparse.urlparse(self.request.uri)
    request_url_without_path = parsed[0] + '://' + parsed[1]
    request_url_without_params = request_url_without_path + parsed[2]

    values = {
      'request': self.request,
      'request_url_without_path': request_url_without_path,
      'request_url_without_params': request_url_without_params,
      'user': users.get_current_user(),
      'login_url': users.create_login_url(self.request.uri),
      'logout_url': users.create_logout_url('/'),
      'debug': self.request.get('deb'),
    }
    values.update(extra_values)
    cwd = os.path.dirname(__file__)
    path = os.path.join(cwd, 'templates', template_name + '.html')
    logging.debug(path)
    self.response.out.write(template.render(path, values, debug=_DEBUG))

  def ReportError(self, message):
    """Shows an error HTML page.

    Args:
      message: string
      A detailed error message.
    """
    args = pprint.pformat(self.ArgsToDict())
    self.Render('error', vars())
    logging.error(message)

  def store_login(self, oidrequest, kind):
    """Stores the details of an OpenID login in the datastore.

    Args:
      oidrequest: OpenIDRequest

      kind: string
      'remembered', 'confirmed', or 'declined'
    """
    assert kind in ['remembered', 'confirmed', 'declined']
    user = users.get_current_user()
    assert user

    login = datastore.Entity('Login')
    login['relying_party'] = oidrequest.trust_root
    login['time'] = datetime.datetime.now()
    login['kind'] = kind
    login['user'] = user
    datastore.Put(login)

  def CheckUser(self):
    """Checks that the OpenID identity being asserted is owned by this user.

    Specifically, checks that the request URI's path is the user's nickname.

    Returns:
      True if the request's path is the user's nickname. Otherwise, False, and
      prints an error page.
    """
    args = self.ArgsToDict()

    user = users.get_current_user()
    if not user:
      # not logged in!
      return False

    # check that the user is logging into their page, not someone else's.
    identity = args['openid.identity']
    parsed = urlparse.urlparse(identity)
    path = parsed[2]

    if path[1:] != user.nickname():
      expected = parsed[0] + '://' + parsed[1] + '/' + user.nickname()
      logging.warning('Bad identity URL %s for user %s; expected %s' %
                      (identity, user.nickname(), expected))
      return False

    logging.debug('User %s matched identity %s' % (user.nickname(), identity))
    return True

  def ShowFrontPage(self):
    """Do an internal (non-302) redirect to the front page.

    Preserves the user agent's requested URL.
    """
    front_page = FrontPage()
    front_page.request = self.request
    front_page.response = self.response
    front_page.get()


class FrontPage(Handler):
  """Show the default OpenID page, with the last 10 logins for this user."""
  def get(self):
    logins = []

    user = users.get_current_user()
    if user:
      query = datastore.Query('Login')
      query['user ='] = user
      query.Order(('time', datastore.Query.DESCENDING))
      logins = query.Get(10)

    self.Render('index', vars())


class Login(Handler):
  """Handles OpenID requests: associate, checkid_setup, checkid_immediate."""

  def get(self):
    """Handles GET requests."""
    user = users.get_current_user()
    if user:
      logging.debug('User: %s' % user)

    login_url = users.create_login_url(self.request.uri)
    logout_url = users.create_logout_url(self.request.uri)

    oidrequest = self.GetOpenIdRequest()
    if oidrequest is False:
      # there was an error, and GetOpenIdRequest displayed it. bail out.
      return
    elif oidrequest is None:
      # this is a request from a browser
      self.ShowFrontPage()
    elif oidrequest.mode in ['checkid_immediate', 'checkid_setup']:
      if self.HasCookie() and user:
        logging.debug('Has cookie, confirming identity to ' +
                      oidrequest.trust_root)
        self.store_login(oidrequest, 'remembered')
        self.Respond(oidrequest.answer(True))
      elif oidrequest.immediate:
        self.store_login(oidrequest, 'declined')
        oidresponse = oidrequest.answer(False, server_url=login_url)
        self.Respond(oidresponse)
      else:
        if self.CheckUser():
          self.Render('prompt', vars())
        else:
          self.ShowFrontPage()

    elif oidrequest.mode in ['associate', 'check_authentication']:
      self.Respond(oidserver.handleRequest(oidrequest))

    else:
      self.ReportError('Unknown mode: %s' % oidrequest.mode)

  post = get

  def prompt(self):
    """Ask the user to confirm an OpenID login request."""
    oidrequest = self.GetOpenIdRequest()
    if oidrequest:
      self.response.out.write(page)


class FinishLogin(Handler):
  """Handle a POST response to the OpenID login prompt form."""
  def post(self):
    if not self.CheckUser():
      self.ShowFrontPage()
      return

    args = self.ArgsToDict()

    try:
      oidrequest = OpenIDServer.CheckIDRequest.fromQuery(args)
    except:
      trace = ''.join(traceback.format_exception(*sys.exc_info()))
      self.ReportError('Error decoding login request:\n%s' % trace)
      return

    if args.has_key('yes'):
      logging.debug('Confirming identity to %s' % oidrequest.trust_root)
      if args.get('remember', '') == 'yes':
        logging.info('Setting cookie to remember openid login for two weeks')

        expires = datetime.datetime.now() + datetime.timedelta(weeks=2)
        expires_rfc822 = expires.strftime('%a, %d %b %Y %H:%M:%S +0000')
        self.response.headers.add_header(
          'Set-Cookie', 'openid_remembered=yes; expires=%s' % expires_rfc822)

      self.store_login(oidrequest, 'confirmed')
      self.Respond(oidrequest.answer(True))

    elif args.has_key('no'):
      logging.debug('Login denied, sending cancel to %s' %
                    oidrequest.trust_root)
      self.store_login(oidrequest, 'declined')
      return self.Respond(oidrequest.answer(False))

    else:
      self.ReportError('Bad login request.')



application = webapp2.WSGIApplication([
  ('/', FrontPage),
  ('/login', FinishLogin),
  ('/[^/]+', Login),
], debug=_DEBUG)
