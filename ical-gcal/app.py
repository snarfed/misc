"""ical-gcal App Engine app.

Munges iCal feeds so that Google Calendar can import them.

Adapted from Keith McCammon's ical-to-gcal.py: http://mccammon.org/keith/code/
"""

__author__ = ['Keith McCammon', 'Ryan Barrett <ical-gcal@ryanb.org>']

import logging
import re
import urllib2

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


# TAGS = [ ('BEGIN:VALARM', 'END:VALARM'),
#          ('BEGIN:VTODO', 'END:VTODO'),
#          ]


class Feed(webapp.RequestHandler):
  def get(self):
    # extract the source feed URL
    assert self.request.path.startswith('/feed/')
    source_url = self.request.path[6:]
    if self.request.query_string:
        source_url += ('?' + self.request.query_string)
    source_url = urllib2.unquote(source_url)

    # fetch the source feed
    logging.info('Fetching %s', source_url)
    resp = urlfetch.fetch(source_url, deadline=999, validate_certificate=False)

    # write to output, removing blank lines
    self.response.headers['Content-Type'] = 'text/calendar'
    munged = re.sub('\n\s*\n', '\n', resp.content)
    munged = re.sub('\nUID:.*\n', '\n', munged)
    self.response.out.write(munged)

    # outfile = []
    # for start, end in TAGS:
    #     logging.info("Begin processing tag set: (%s, %s)\n", start, end)

    #     # If there's already data in outfile, assume that we need to continue
    #     # processing that data, with additional tag sets.
    #     if len(outfile) > 0:
    #         data = outfile[:]
    #         outfile = []
    #     else:
    #         data = infile

    #     # Remove lines that either match or are between start and end tags.
    #     within = False
    #     for i in data:
    #         if not within and start not in i and end not in i:
    #             outfile.append(i)
    #         elif start in i:
    #             logging.debug("Entering stanza: %s\n", start)
    #             within = True
    #         elif within:
    #             if end in i:
    #                 logging.debug("Exiting stanza: %s\n", end)
    #                 within = False
    #             else:
    #                 logging.debug("--> within stanza\n")

    #     logging.info("End processing tag set: (%s, %s)\n", start, end)

    # logging.info("Removed %d lines.", len(infile) - len(outfile))


application = webapp.WSGIApplication([('/feed/.*', Feed)], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
