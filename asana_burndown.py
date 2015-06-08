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
START = datetime.date(2015, 5, 12)


def parse(date_str):
  return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')


def main():
  tasks = {t['id']: t for t in json.load(sys.stdin)['data']}

  #
  # step 1: fetch history of each task from Asana API
  #
  headers = {'Authorization': 'Basic %s' %
             base64.encodestring('%s:' % sys.argv[1]).replace('\n', '')}

  # maps task id (int) to list of story dicts
  history = {}
  history_lock = threading.Lock()

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
  for id in tasks:
    thread = threading.Thread(target=get_history, args=(id,))
    threads.append(thread)
    thread.start()

  for thread in threads:
    thread.join()

  sys.stderr.write('\n')

  # uncomment to read/write task history to/from disk
  #
  # with open('/Users/ryan/hist.json', 'w') as f:
  #   f.write(json.dumps(history, indent=2))

  # with open('/Users/ryan/hist.json') as f:
  #   history = {int(k): v for k, v in json.loads(f.read()).items()}

  #
  # step 2: generate calendars of when each task was created and completed
  #
  # these map datetime.date to list of task dicts
  by_created = collections.defaultdict(list)
  by_completed = collections.defaultdict(list)

  for task in tasks.values():
    # record creation and completion date
    created = task['last_change'] = parse(task['created_at']).date()
    by_created[created].append(task)
    if task['completed']:
      by_completed[parse(task['completed_at']).date()].append(task)

    # record priority and size
    task['orig_priority'] = 'Z'  # so it sorts after P*
    task['orig_size'] = DEFAULT_SIZE
    for tag in task.get('tags', []):
      name = tag['name']
      if name in PRIORITIES:
        task['orig_priority'] = name
      elif name.endswith('pts'):
        task['orig_size'] = float(name[:-3].strip())

    task['cur_priority'] = task['orig_priority']
    task['cur_size'] = task['orig_size']

  #
  # step 3: generate calendar of when tasks changed priority or size
  #
  # these map datetime.date to dict of task id to string priority or float size
  changed_priority = collections.defaultdict(dict)
  changed_size = collections.defaultdict(dict)

  for id, stories in history.items():
    for story in sorted(stories, key=lambda s: parse(s['created_at'])):
      if story['type'] != 'system':
        continue
      prefix = 'added to '
      if story['text'].startswith(prefix):
        tag = story['text'][len(prefix):]
        date = parse(story['created_at']).date()
        if tag in PRIORITIES:
          changed_priority[date][id] = tag
        elif tag.endswith('pts'):
          changed_size[date][id] = float(tag[:-3].strip())

  #
  # step 4: walk dates, keep track of point sums per priority, and write CSV rows
  #
  # these map priority (including None) to point sum
  original = collections.defaultdict(float)
  extra = collections.defaultdict(float)

  # CSV header
  writer = csv.writer(sys.stdout, delimiter='\t')
  writer.writerow(('Date',) + tuple(itertools.chain(*((p, p + ' new')
                                                      for p in PRIORITIES))))

  day = datetime.timedelta(days=1)
  cur = min(min(by_completed), START - day)
  end = max(by_completed)

  def from_ledger(task):
    return original if task['last_change'] <= START else extra

  while cur <= end:
    cur += day
    to_ledger = original if cur <= START else extra

    for task in by_created[cur]:
      to_ledger[task['cur_priority']] += task['cur_size']

    for task in by_completed[cur - day]:  # count tasks completed on the day *after*
      from_ledger(task)[task['cur_priority']] -= task['cur_size']

    for id, new_priority in changed_priority[cur].items():
      task = tasks[id]
      to_ledger[new_priority] += task['cur_size']
      from_ledger(task)[task['cur_priority']] -= task['cur_size']
      task['cur_priority'] = new_priority
      task['last_change'] = cur

    for id, new_size in changed_size[cur].items():
      task = tasks[id]
      to_ledger[task['cur_priority']] += new_size
      from_ledger(task)[task['cur_priority']] -= task['cur_size']
      task['cur_size'] = new_size
      task['last_change'] = cur

    if cur >= START - day and cur.weekday() < 5:  # not weekend
      writer.writerow((cur,) + tuple(itertools.chain(*((original[p], extra[p])
                                                       for p in PRIORITIES))))


if __name__ == '__main__':
  main()

