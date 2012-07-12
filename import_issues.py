#!/usr/bin/python
"""Imports issues into a Google Code project hosting issue tracker from CSV.

Usage: import_issues.py PROJECT FILENAME

where PROJECT is the Google Code project name and FILENAME is the CSV file to
import.

The CSV columns are: title, content, author, status, owner, labels, cc.
Title, content, and author are required, but the rest are optional, so the file
may have anywhere from 3 to 7 columns. If the file has a header with the column
names above, it will be skipped. Leading and trailing whitespace will be trimmed
from fields. Labels and cc are space- or comma-separated lists of values. If
comma-separated, the entire field must be enclosed in quotes."""
"""
Requires python-gdata (Google's Python GData client library) 2.0.7 or higher. If
you don't already have it, here are commands to download and install it in the
same directory as this script:

wget http://gdata-python-client.googlecode.com/files/gdata-2.0.15.tar.gz
tar xzf gdata-2.0.15.tar.gz
ln -s gdata-2.0.15/src/gdata
ln -s gdata-2.0.15/src/atom

import_issues.py is in the public domain.

Changelog:
0.2 11/14/2011
- parse and validate the CSV file first
0.1 11/11/2011
- first release!
"""

__author__ = ['Ryan Barrett <import_issues@ryanb.org>']

import BaseHTTPServer
import csv
import itertools
import string
import sys
import urlparse
import webbrowser

from gdata.projecthosting import client
from gdata import gauth


CLIENT_ID = '396649679464.apps.googleusercontent.com'
CLIENT_SECRET = 'BJnfbAhVja3Ffh6tfwyhnGMH'
HEADER = ['title', 'content', 'author', 'status', 'owner', 'labels', 'cc']
REQUIRED_COLUMNS = (0, 1, 2)  # 0-based
LIST_COLUMNS = (5, 6)  # 0-based; indexes of columns that are lists of values


def print_and_flush(str):
  sys.stdout.write(str)
  sys.stdout.flush()

def main(args):
  if len(args) != 2:
    print __doc__
    sys.exit(1)

  project, filename = args

  # read, normalize, and validate CSV file
  with open(filename) as f:
    rows = list(csv.reader(f, skipinitialspace=True))

  passed = True
  for i, row in enumerate(rows):
    for c in REQUIRED_COLUMNS:
      if not row[c]:
        passed = False
        print >> sys.stderr, 'Error on line %d: Missing required field %s' % (
          i + 1, HEADER[c + 1])

  if not passed:
    sys.exit(1)

  # local web server that handles the oauth token redirect. (port 0 means pick
  # any available port.)
  server = BaseHTTPServer.HTTPServer(('localhost', 0), OAuthRedirectHandler)
  redirect_url = 'http://%s:%d' % server.server_address

  # start oauth: get a request token
  phc = client.ProjectHostingClient()
  request_token = phc.get_oauth_token(
    gauth.AUTH_SCOPES['code'], redirect_url, CLIENT_ID, CLIENT_SECRET)
  print """\
Opening a web page in your browser to request access.
Please click the Grant access button."""
  webbrowser.open_new_tab(str(request_token.generate_authorization_url()))

  # listen for the redirect
  server.handle_request()

  # finish oauth: get an access token
  gauth.authorize_request_token(request_token, OAuthRedirectHandler.url)
  access_token = phc.get_access_token(request_token)

  # import the issues, one at a time
  try:
    for i, row in enumerate(rows):
      if i == 0 and map(string.lower, row) == HEADER:
        continue

      for c in LIST_COLUMNS:
        if c < len(row):
          # split on comma and space. filter out empty strings.
          values = map(string.strip, row[c].split(', '))
          row[c] = list(itertools.ifilter(bool, values))

      phc.add_issue(project, *row, auth_token=access_token)
      print_and_flush('.')
  except:
    print >> sys.stderr, '\nError on line %d:\n%s' % (i + 1, row)
    raise
  finally:
    print '\nImported %d issues.' % (i + 1)


class OAuthRedirectHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """Local HTTP request handler that handles the oauth token redirect.
  Stores the token in the token class attribute.
  """
  def do_GET(self):
    OAuthRedirectHandler.url = self.path
    self.send_response(200)
    self.wfile.write('<script type="text/javascript"> window.close() </script>')

  # suppress request logging
  def log_request(self, *args): pass

if __name__ == '__main__':
  main(sys.argv[1:])
