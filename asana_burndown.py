#!/usr/bin/env python
"""Convert Asana data into a day-by-day CSV file to generate a burndown chart.

Usage: asana_burndown.py <API_KEY>

Reads Asana's exported JSON from stdin. Writes CSV data to stdout that can be
imported into a spreadsheet (e.g. Google Sheets) to generate a burndown chart.

Inspired by https://github.com/ckalima/asana-tools

Asana API docs:
https://asana.com/developers/documentation/getting-started
https://asana.com/developers/api-reference
"""

import base64
import collections
import csv
import datetime
import itertools
import json
import sys
import threading
import urllib2

PRIORITIES = ('P0', 'P1', 'P2', 'Z')
DEFAULT_SIZE = 2.0
START = datetime.date(2015, 5, 11)


def parse(date_str):
  return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ').date()


def main():
  tasks = json.load(sys.stdin)['data']

  # HTTP basic auth for Asana API
  headers = {'Authorization': 'Basic %s' %
             base64.encodestring('%s:' % sys.argv[1]).replace('\n', '')}

  # maps task id (int) to history JSON dict
  history = {}
  history_lock = threading.Lock()

  # fetch task history ("stories" in asana terminology)
  #
  # example story:
  #   {
  #      "created_at" : "2015-05-08T19:35:22.842Z",
  #      "type" : "system",
  #      "created_by" : {
  #         "name" : "Nish Bhat",
  #         "id" : 6503456116052
  #      },
  #      "text" : "added to Bioinformatics",
  #      "id" : 33571348387449
  #   }
  #
  # other possible text: "removed from P2", "completed this task", etc
  #
  sys.stderr.write('Fetching task history')
  def get_history(id):
    req = urllib2.Request('https://app.asana.com/api/1.0/tasks/%s/stories' % id,
                          headers=headers)
    try:
      hist = json.loads(urllib2.urlopen(req).read())['data']
    except urllib2.HTTPError, e:
      print >> sys.stderr, 'Broke on task %r: %s %s' % (
        id, e.code, e.read() or getattr(e, 'body'))
      raise
    with history_lock:
      history[id] = hist
    sys.stderr.write('.')

  threads = []
  for task in tasks:
    thread = threading.Thread(target=get_history, args=(task['id'],))
    threads.append(thread)
    thread.start()

  for task in tasks:
    thread.join()


  # XXX NOCOMMIT
  with open('/Users/ryan/hist.json') as f:
    f.write(json.dumps(history))


  # maps datetime.date to JSON task dict
  by_created = collections.defaultdict(list)
  by_completed = collections.defaultdict(list)

  for task in tasks:
    # record creation and completion date
    by_created[parse(task['created_at'])].append(task)
    if task['completed']:
      by_completed[parse(task['completed_at'])].append(task)

    # record priority and size
    task['priority'] = 'Z'  # so it sorts after Px
    task['size'] = DEFAULT_SIZE
    for tag in task.get('tags', []):
      name = tag['name']
      if name in PRIORITIES:
        task['priority'] = name
      elif name.endswith('pts'):
        task['size'] = float(name[:-3])

  # maps datetime.date to dict of int task id to string priority or float size
  new_priority = collections.defaultdict(dict)
  old_priority = collections.defaultdict(dict)
  new_size = collections.defaultdict(dict)
  old_size = collections.defaultdict(dict)

  for id, stories in history.items():
    for story in stories:
      if story['type'] != 'system':
        return
      date = parse(story['created_at'])
      for prefix, priority, size in (('added to ', new_priority, new_size),
                                     ('removed to ', old_priority, old_size)):
        if story['text'].startswith(prefix):
          tag = story['text'][len(prefix):]
          if tag in PRIORITIES:
            priority[date][id] = tag
          elif tag.endswith('pts'):
            size[date][id] = float(tag[:-3])

  # maps priority (including None) to point sum
  original = collections.defaultdict(float)
  extra = collections.defaultdict(float)

  # CSV header
  writer = csv.writer(sys.stdout)
  writer.writerow(('Date',) + tuple(itertools.chain(*((p, p + ' new')
                                                      for p in PRIORITIES))))

  # walk dates and output counts
  day = datetime.timedelta(days=1)
  cur = min(min(by_completed), START - day)
  end = max(by_completed)

  while cur <= end:
    cur += day
    if cur.weekday() >= 5:
      continue  # weekend
    for task in by_created[cur]:
      ledger = original if cur <= START else extra
      ledger[task['priority']] += task['size']
    for task in by_completed[cur - day]:
      ledger = original if parse(task['created_at']) <= START else extra
      ledger[task['priority']] -= task['size']
    if cur >= START - day:
      writer.writerow((cur,) + tuple(itertools.chain(*((original[p], extra[p])
                                                       for p in PRIORITIES))))


if __name__ == '__main__':
  main()

