"""
This module contains an C{L{OpenIDStore}} implementation backed by
flat files.
"""

import string
import os
import os.path
import sys
import time

from errno import EEXIST, ENOENT

try:
    from tempfile import mkstemp
except ImportError:
    # Python < 2.3
    import tempfile
    import warnings
    warnings.filterwarnings("ignore",
                            "tempnam is a potential security risk",
                            RuntimeWarning,
                            "openid.store.filestore")

    def mkstemp(dir):
        for _ in range(5):
            name = os.tempnam(dir)
            try:
                fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0600)
            except OSError, why:
                if why[0] != EEXIST:
                    raise
            else:
                return fd, name

        raise RuntimeError('Failed to get temp file after 5 attempts')

from openid.association import Association
from openid.store.interface import OpenIDStore
from openid import cryptutil, oidutil

_filename_allowed = string.ascii_letters + string.digits + '.'
try:
    # 2.4
    set
except NameError:
    try:
        # 2.3
        import sets
    except ImportError:
        # Python < 2.2
        d = {}
        for c in _filename_allowed:
            d[c] = None
        _isFilenameSafe = d.has_key
        del d
    else:
        _isFilenameSafe = sets.Set(_filename_allowed).__contains__
else:
    _isFilenameSafe = set(_filename_allowed).__contains__

def _safe64(s):
    h64 = oidutil.toBase64(cryptutil.sha1(s))
    h64 = h64.replace('+', '_')
    h64 = h64.replace('/', '.')
    h64 = h64.replace('=', '')
    return h64

def _filenameEscape(s):
    filename_chunks = []
    for c in s:
        if _isFilenameSafe(c):
            filename_chunks.append(c)
        else:
            filename_chunks.append('_%02X' % ord(c))
    return ''.join(filename_chunks)

def _removeIfPresent(filename):
    """Attempt to remove a file, returning whether the file existed at
    the time of the call.

    str -> bool
    """
    try:
        os.unlink(filename)
    except OSError, why:
        if why[0] == ENOENT:
            # Someone beat us to it, but it's gone, so that's OK
            return 0
        else:
            raise
    else:
        # File was present
        return 1

def _ensureDir(dir_name):
    """Create dir_name as a directory if it does not exist. If it
    exists, make sure that it is, in fact, a directory.

    Can raise OSError

    str -> NoneType
    """
    try:
        os.makedirs(dir_name)
    except OSError, why:
        if why[0] != EEXIST or not os.path.isdir(dir_name):
            raise

class FileOpenIDStore(OpenIDStore):
    """
    This is a filesystem-based store for OpenID associations and
    nonces.  This store should be safe for use in concurrent systems
    on both windows and unix (excluding NFS filesystems).  There are a
    couple race conditions in the system, but those failure cases have
    been set up in such a way that the worst-case behavior is someone
    having to try to log in a second time.

    Most of the methods of this class are implementation details.
    People wishing to just use this store need only pay attention to
    the C{L{__init__}} method.

    Methods of this object can raise OSError if unexpected filesystem
    conditions, such as bad permissions or missing directories, occur.
    """

    def __init__(self, directory):
        """
        Initializes a new FileOpenIDStore.  This initializes the
        nonce and association directories, which are subdirectories of
        the directory passed in.

        @param directory: This is the directory to put the store
            directories in.

        @type directory: C{str}
        """
        # Make absolute
        directory = os.path.normpath(os.path.abspath(directory))

        self.nonce_dir = os.path.join(directory, 'nonces')

        self.association_dir = os.path.join(directory, 'associations')

        # Temp dir must be on the same filesystem as the assciations
        # directory and the directory containing the auth key file.
        self.temp_dir = os.path.join(directory, 'temp')

        self.auth_key_name = os.path.join(directory, 'auth_key')

        self.max_nonce_age = 6 * 60 * 60 # Six hours, in seconds

        self._setup()

    def _setup(self):
        """Make sure that the directories in which we store our data
        exist.

        () -> NoneType
        """
        _ensureDir(os.path.dirname(self.auth_key_name))
        _ensureDir(self.nonce_dir)
        _ensureDir(self.association_dir)
        _ensureDir(self.temp_dir)

    def _mktemp(self):
        """Create a temporary file on the same filesystem as
        self.auth_key_name and self.association_dir.

        The temporary directory should not be cleaned if there are any
        processes using the store. If there is no active process using
        the store, it is safe to remove all of the files in the
        temporary directory.

        () -> (file, str)
        """
        fd, name = mkstemp(dir=self.temp_dir)
        try:
            file_obj = os.fdopen(fd, 'wb')
            return file_obj, name
        except:
            _removeIfPresent(name)
            raise

    def readAuthKey(self):
        """Read the auth key from the auth key file. Will return None
        if there is currently no key.

        () -> str or NoneType
        """
        try:
            auth_key_file = file(self.auth_key_name, 'rb')
        except IOError, why:
            if why[0] == ENOENT:
                return None
            else:
                raise

        try:
            return auth_key_file.read()
        finally:
            auth_key_file.close()

    def createAuthKey(self):
        """Generate a new random auth key and safely store it in the
        location specified by self.auth_key_name.

        () -> str"""

        # Do the import here because this should only get called at
        # most once from each process. Once the auth key file is
        # created, this should not get called at all.
        auth_key = cryptutil.randomString(self.AUTH_KEY_LEN)

        file_obj, tmp = self._mktemp()
        try:
            file_obj.write(auth_key)
            # Must close the file before linking or renaming it on win32.
            file_obj.close()

            try:
                if hasattr(os, 'link') and sys.platform != 'cygwin':
                    # because os.link works in some cygwin environments,
                    # but returns errno 17 on others.  Haven't figured out
                    # how to predict when it will do that yet.
                    os.link(tmp, self.auth_key_name)
                else:
                    os.rename(tmp, self.auth_key_name)
            except OSError, why:
                if why[0] == EEXIST:
                    auth_key = self.readAuthKey()
                    if auth_key is None:
                        # This should only happen if someone deletes
                        # the auth key file out from under us.
                        raise
                else:
                    raise
        finally:
            file_obj.close()
            _removeIfPresent(tmp)

        return auth_key

    def getAuthKey(self):
        """Retrieve the auth key from the file specified by
        self.auth_key_name, creating it if it does not exist.

        () -> str
        """
        auth_key = self.readAuthKey()
        if auth_key is None:
            auth_key = self.createAuthKey()

        if len(auth_key) != self.AUTH_KEY_LEN:
            fmt = ('Got an invalid auth key from %s. Expected %d byte '
                   'string. Got: %r')
            msg = fmt % (self.auth_key_name, self.AUTH_KEY_LEN, auth_key)
            raise ValueError(msg)

        return auth_key

    def getAssociationFilename(self, server_url, handle):
        """Create a unique filename for a given server url and
        handle. This implementation does not assume anything about the
        format of the handle. The filename that is returned will
        contain the domain name from the server URL for ease of human
        inspection of the data directory.

        (str, str) -> str
        """
        if server_url.find('://') == -1:
            raise ValueError('Bad server URL: %r' % server_url)

        proto, rest = server_url.split('://', 1)
        domain = _filenameEscape(rest.split('/', 1)[0])
        url_hash = _safe64(server_url)
        if handle:
            handle_hash = _safe64(handle)
        else:
            handle_hash = ''

        filename = '%s-%s-%s-%s' % (proto, domain, url_hash, handle_hash)

        return os.path.join(self.association_dir, filename)

    def storeAssociation(self, server_url, association):
        """Store an association in the association directory.

        (str, Association) -> NoneType
        """
        association_s = association.serialize()
        filename = self.getAssociationFilename(server_url, association.handle)
        tmp_file, tmp = self._mktemp()

        try:
            try:
                tmp_file.write(association_s)
                os.fsync(tmp_file.fileno())
            finally:
                tmp_file.close()

            try:
                os.rename(tmp, filename)
            except OSError, why:
                if why[0] != EEXIST:
                    raise

                # We only expect EEXIST to happen only on Windows. It's
                # possible that we will succeed in unlinking the existing
                # file, but not in putting the temporary file in place.
                try:
                    os.unlink(filename)
                except OSError, why:
                    if why[0] == ENOENT:
                        pass
                    else:
                        raise

                # Now the target should not exist. Try renaming again,
                # giving up if it fails.
                os.rename(tmp, filename)
        except:
            # If there was an error, don't leave the temporary file
            # around.
            _removeIfPresent(tmp)
            raise

    def getAssociation(self, server_url, handle=None):
        """Retrieve an association. If no handle is specified, return
        the association with the latest expiration.

        (str, str or NoneType) -> Association or NoneType
        """
        if handle is None:
            handle = ''

        # The filename with the empty handle is a prefix of all other
        # associations for the given server URL.
        filename = self.getAssociationFilename(server_url, handle)

        if handle:
            return self._getAssociation(filename)
        else:
            association_files = os.listdir(self.association_dir)
            matching_files = []
            # strip off the path to do the comparison
            name = os.path.basename(filename)
            for association_file in association_files:
                if association_file.startswith(name):
                    matching_files.append(association_file)

            matching_associations = []
            # read the matching files and sort by time issued
            for name in matching_files:
                full_name = os.path.join(self.association_dir, name)
                association = self._getAssociation(full_name)
                if association is not None:
                    matching_associations.append(
                        (association.issued, association))

            matching_associations.sort()

            # return the most recently issued one.
            if matching_associations:
                (_, assoc) = matching_associations[-1]
                return assoc
            else:
                return None

    def _getAssociation(self, filename):
        try:
            assoc_file = file(filename, 'rb')
        except IOError, why:
            if why[0] == ENOENT:
                # No association exists for that URL and handle
                return None
            else:
                raise
        else:
            try:
                assoc_s = assoc_file.read()
            finally:
                assoc_file.close()

            try:
                association = Association.deserialize(assoc_s)
            except ValueError:
                _removeIfPresent(filename)
                return None

        # Clean up expired associations
        if association.getExpiresIn() == 0:
            _removeIfPresent(filename)
            return None
        else:
            return association

    def removeAssociation(self, server_url, handle):
        """Remove an association if it exists. Do nothing if it does not.

        (str, str) -> bool
        """
        assoc = self.getAssociation(server_url, handle)
        if assoc is None:
            return 0
        else:
            filename = self.getAssociationFilename(server_url, handle)
            return _removeIfPresent(filename)

    def storeNonce(self, nonce):
        """Mark this nonce as present.

        str -> NoneType
        """
        filename = os.path.join(self.nonce_dir, nonce)
        nonce_file = file(filename, 'w')
        nonce_file.close()

    def useNonce(self, nonce):
        """Return whether this nonce is present. As a side effect,
        mark it as no longer present.

        str -> bool
        """
        filename = os.path.join(self.nonce_dir, nonce)
        try:
            st = os.stat(filename)
        except OSError, why:
            if why[0] == ENOENT:
                # File was not present, so nonce is no good
                return 0
            else:
                raise
        else:
            # Either it is too old or we are using it. Either way, we
            # must remove the file.
            try:
                os.unlink(filename)
            except OSError, why:
                if why[0] == ENOENT:
                    # someone beat us to it, so we cannot use this
                    # nonce anymore.
                    return 0
                else:
                    raise

            now = time.time()
            nonce_age = now - st.st_mtime

            # We can us it if the age of the file is less than the
            # expiration time.
            return nonce_age <= self.max_nonce_age

    def clean(self):
        """Remove expired entries from the database. This is
        potentially expensive, so only run when it is acceptable to
        take time.

        () -> NoneType
        """
        nonces = os.listdir(self.nonce_dir)
        now = time.time()

        # Check all nonces for expiry
        for nonce in nonces:
            filename = os.path.join(self.nonce_dir, nonce)
            try:
                st = os.stat(filename)
            except OSError, why:
                if why[0] == ENOENT:
                    # The file did not exist by the time we tried to
                    # stat it.
                    pass
                else:
                    raise
            else:
                # Remove the nonce if it has expired
                nonce_age = now - st.st_mtime
                if nonce_age > self.max_nonce_age:
                    _removeIfPresent(filename)

        association_filenames = os.listdir(self.association_dir)
        for association_filename in association_filenames:
            try:
                association_file = file(association_filename, 'rb')
            except IOError, why:
                if why[0] == ENOENT:
                    pass
                else:
                    raise
            else:
                try:
                    assoc_s = association_file.read()
                finally:
                    association_file.close()

                # Remove expired or corrupted associations
                try:
                    association = Association.deserialize(assoc_s)
                except ValueError:
                    _removeIfPresent(association_filename)
                else:
                    if association.getExpiresIn() == 0:
                        _removeIfPresent(association_filename)
