#!/usr/bin/python

"""Publishes a JSON Google+ post to WordPress via XML-RPC.

This script converts the JSON representation of a Google+ post, as returned by
the API or https://google.com/takeout , to Markdown. Comments are converted and
written to separate files. Given the input file my_post.json for a post made on
8/29/2012, the output post file is written to 2012-08-29_my_post.txt.

This script is in the public domain.
"""

__author__ = 'Ryan Barrett <public@ryanb.org>'

import json
import os.path
import sys


def main(args):
  if len(args) != 2:
    print >> sys.stderr, 'Usage: google_plus_json_to_markdown.py FILENAME'
    return 1

  infile = args[1]
  with open(infile) as f:
    post = json.loads(f.read())

  date = post['published'][:10] # 4 digit year, 2 digits month and day, 2 dashes
  postfile = '%s_%s.txt' % (date, os.path.splitext(infile)[0])
  with open(postfile, 'w') as f:
    print >> f, post['title']
    print >> f
    print >> f, post['object']['content']

  for comment in post.get('replies', {}).get('items', []):
    comment['']

if __name__ == '__main__':
  main(sys.argv)
