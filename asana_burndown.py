#!/usr/bin/env python
"""Convert Asana data into a day-by-day CSV file to generate a burndown chart.

Reads Asana's exported JSON from stdin. Writes CSV data to stdout that can be
imported into a spreadsheet (e.g. Google Sheets) to generate a burndown chart.

Inspired by https://github.com/ckalima/asana-tools
"""

import collections
import csv
import datetime
import itertools
import json
import sys

PRIORITIES = ('P0', 'P1', 'P2', 'Z')
DEFAULT_SIZE = 1.0
START = datetime.date(2015, 5, 11)


def parse(date_str):
  return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ').date()


def main():
  tasks = json.load(sys.stdin)['data']

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

  # maps priority (including None) to point sum
  original = collections.defaultdict(float)
  extra = collections.defaultdict(float)

  # CSV header
  writer = csv.writer(sys.stdout)
  writer.writerow(('Date',) + tuple(itertools.chain(*((p, p + ' new')
                                                      for p in PRIORITIES))))

  # walk dates and output counts
  day = datetime.timedelta(days=1)
  end = max(by_completed)
  cur = START

  while cur <= end:
    if cur.isoweekday() >= 6:
      continue  # weekend
    for task in by_created[cur]:
      ledger = original if cur <= START else extra
      ledger[task['priority']] += task['size']
    for task in by_completed[cur - day]:
      ledger = original if parse(task['created_at']) <= START else extra
      ledger[task['priority']] -= task['size']
    writer.writerow((cur,) + tuple(itertools.chain(*((original[p], extra[p])
                                                     for p in PRIORITIES))))
    cur += day


if __name__ == '__main__':
  main()

