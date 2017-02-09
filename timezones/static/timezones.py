#!/usr/bin/python
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""
A test app for converting datetimes between timezones and storing and
retrieving them from the datastore.
"""

__author__ = 'ryanb@google.com (Ryan Barrett)'

from google.appengine.ext import webapp
from google.appengine.api import datastore

import calendar
import datetime
import os
import pytz
import sys
import time
import wsgiref.handlers


HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head>
<title>Time zones in Google App Engine</title>
<style type="text/css">
body {
  width: 700px;
  margin: 15px;
}

table {
  border: 1px solid Navy;
  padding: 10px;
}

.form { background-color: LightSteelBlue; }
.results { background-color: Ivory; }
.results .even { background-color: FloralWhite; }
</style>

</head>

<body>
<h1> Time zones in Google App Engine </h1>

<p> Use this to try out time zone handling in the
<a href="http://appengine.google.com/">Google App Engine</a> runtime and
datastore. See the
 <a href="http://code.google.com/appengine/docs/datastore/typesandpropertyclasses.html#DateTimeProperty">DateTimeProperty docs</a> for details.
You can also <a href="/static/timezones.py">download this app's source</a>.
</p>

<p> The runtime's <code>TZ</code> environment variable is set to
<code>UTC</code>, and can't be changed. Timestamps returned by e.g.
<a href="http://python.org/doc/lib/module-time.html#l2h-2829"><code>time.time()</code></a>
and
<a href="http://python.org/doc/lib/datetime-datetime.html#l2h-636"><code>datetime.datetime.now()</code></a>
will always be in UTC.
Similarly,
<a href="http://python.org/doc/lib/datetime-datetime.html"><code>datetime</code></a>
properties in the datastore will always be stored and returned as UTC.
</p>

<p>
You can change the time zone of a <code>datetime</code> in memory with the
<a href="http://python.org/doc/lib/datetime-datetime.html#l2h-658"><code>astimezone()</code></a>
method. If <code>datetime</code>'s
<a href="http://python.org/doc/lib/datetime-tzinfo.html"><code>tzinfo</code></a>
member isn't set, you'll first need to set it to a UTC <code>tzinfo</code>
with the
<a href="http://python.org/doc/lib/datetime-datetime.html#l2h-657"><code>replace()</code></a>
method.
</p>

<p>
The third-party
<a href="http://www.google.com/url?sa=D&q=http://pytz.sourceforge.net/">pytz</a>
module has a comprehensive set of <code>tzinfo</code> classes. If your app has
complex time zone needs, consider including it with your app's code. It's
heavyweight, though - over 500 files! - so if you have simpler needs, consider
writing just the few <code>tzinfo</code> classes you need by hand, following
the <a href="http://python.org/doc/lib/datetime-tzinfo.html">spec</a>.
</p>

<p> In the table below, if a datetime has a <code>+HH:MM</code> or
<code>-HH:MM</code> suffix, e.g. <code>+00:00</code> for UTC, that means it
has a <code>tzinfo</code> (an explicit time zone) attached. Also, assume
<code>utc</code> is a <code>tzinfo</code> for the UTC time zone, and assume
the <code>Foo</code> class has this definition:<br />
<pre>class Foo(db.Model):
  timestamp = db.DateTimeProperty(auto_now=True)
</pre>
<br />
</p>

<table class="results"><tr class="odd">
<td><code>os.environ['TZ']</code></td>
<td>%(env_tz)s</td>
</tr><tr class="even">
<td><code>time.time()</code></td>
<td>%(time_time)s</td>
</tr><tr class="odd">
<td><code>datetime.now()</code></td>
<td>%(datetime_now)s</td>
</tr><tr class="even">
<td><code>Foo().put().timestamp</code></td>
<td>%(after_put)s</td>
</tr><tr class="odd">
<td>Raw timestamp in datastore</td>
<td>%(raw_timestamp)s</td>
</tr><tr class="even">
<td><code>datetime.fromtimestamp(raw_timestamp, utc)</code></td>
<td>%(raw_datetime)s</td>
</tr><tr class="odd">
<td><code>Foo.get(foo_key).timestamp</code></td>
<td>%(after_get)s</td>
</tr><tr class="even">
<td><code>%(translate_code)s</code></td>
<td>%(translated)s</td>
</tr>
</table>

<br />
<form action="/" method="get">

<table class="form"><tr><td>
Translate to
</td><td>
<select name="translate_to" />
  <option %(translate_to_nothing_selected)s value="nothing">nothing</option>
  <option %(translate_to_pst_selected)s value="pst">US/Pacific</option>
  <option %(translate_to_est_selected)s value="est">US/Eastern</option>
  <option %(translate_to_utc_selected)s value="utc">UTC</option>
</select>
</td></tr>

<tr><td>
Translate with
</td><td>
<select name="translate_with">
  <option %(translate_with_astimezone_selected)s value="astimezone">
    astimezone()</option>
  <option %(translate_with_pytz_selected)s value="pytz">
    astimezone() and pytz</option>
  <option %(translate_with_environ_selected)s value="environ">
    os.environ['TZ'] (won't work!)</option>
</select>
</td></tr>

<tr><td></td><td>
<input type="submit" value="Go" />
</td></tr>
</table>
</form>

</body>
</html>
"""


class UtcTzinfo(datetime.tzinfo):
  def utcoffset(self, dt): return datetime.timedelta(0)
  def dst(self, dt): return datetime.timedelta(0)
  def tzname(self, dt): return 'UTC'
  def olsen_name(self): return 'UTC'

class EstTzinfo(datetime.tzinfo):
  def utcoffset(self, dt): return datetime.timedelta(hours=-5)
  def dst(self, dt): return datetime.timedelta(0)
  def tzname(self, dt): return 'EST+05EDT'
  def olsen_name(self): return 'US/Eastern'

class PstTzinfo(datetime.tzinfo):
  def utcoffset(self, dt): return datetime.timedelta(hours=-8)
  def dst(self, dt): return datetime.timedelta(0)
  def tzname(self, dt): return 'PST+08PDT'
  def olsen_name(self): return 'US/Pacific'

TZINFOS = {
  'utc': UtcTzinfo(),
  'est': EstTzinfo(),
  'pst': PstTzinfo(),
}


class App(webapp.RequestHandler):

  def get(self):
    env_tz = os.environ.get('TZ', 'not set')

    # calculate result datetimes
    time_time = time.time()
    datetime_now = datetime.datetime.now()

    entity = datastore.Entity('Datetime')
    entity['datetime'] = datetime_now
    datastore.Put(entity)
    after_put = entity['datetime']

    raw_timestamp = \
        float(entity._ToPb().property(0).value().int64value()) / 1000000
    raw_datetime = \
        datetime.datetime.fromtimestamp(raw_timestamp, TZINFOS['utc'])

    got = datastore.Get(entity)
    after_get = got['datetime']

    translate_code, translated = self.translate(after_get)

    # render
    template_vars = locals()

    template_vars.update(dict(('translate_to_%s_selected' % to, '')
                              for to in ('nothing', 'utc', 'pst', 'est')))
    template_vars['translate_to_%s_selected' %
                  self.request.get('translate_to')] = 'selected="selected"'

    template_vars.update(dict(('translate_with_%s_selected' % with_, '')
                              for with_ in ('nothing', 'astimezone',
                                            'pytz', 'environ')))
    template_vars['translate_with_%s_selected' %
                  self.request.get('translate_with')] = 'selected="selected"'
    self.response.out.write(HTML % template_vars)

  def translate(self, timestamp):
    """Translates a UTC datetime to the env_tz query parameter's time zone.

    Args:
      timestamp: A datetime instance.

    Returns:
      A (str, datetime) tuple. The string is the code snippet used to
      translate the timestamp, and the datetime is the result.
    """
    translate_to = self.request.get('translate_to', 'nothing')
    translate_with = self.request.get('translate_with', 'astimezone()')
    utc = TZINFOS['utc']

    if translate_to == 'nothing':
      return ('no translation', 'N/A')
    elif translate_with == 'astimezone':
      timestamp = timestamp.replace(tzinfo=utc)
      return ('timestamp.astimezone(to_tzinfo)',
              timestamp.astimezone(TZINFOS[translate_to]))
    elif translate_with == 'pytz':
      timestamp = timestamp.replace(tzinfo=utc)
      olsen_name = TZINFOS[translate_to].olsen_name()
      return ('timestamp.astimezone(pytz.timezone(%r))' % olsen_name,
              timestamp.astimezone(pytz.timezone(olsen_name)))
    elif translate_with == 'environ':
      # won't work; for example only
      os.environ['TZ'] = utc.tzname(False)
      time.tzset()
      return ("""os.environ['TZ'] = '%s' <br />
                   time.tzset() <br />
                   time.ctime(raw_timestamp)""" % os.environ['TZ'],
              time.ctime(calendar.timegm(timestamp.timetuple())))
    else:
      return ('invalid translation', 'invalid translation')


def main(argv):
  application = webapp.WSGIApplication([('/', App)], debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main(sys.argv)
