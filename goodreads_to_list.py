#!/usr/bin/python
"""Reads a GoodReads CSV export and converts some to my Markdown list format."""

import csv


def render(books):
  for b in books:
    print '  * [%(Author)s - %(Title)s](http://books.google.com/books?isbn=%(ISBN13)s)' % b
    rating = int(b['My Rating'])
    if rating:
      print '<ok>' if rating == 3 else '<good>' if rating > 3 else '<bad>'
    if b['Exclusive Shelf'] == 'didn-t-finish':
      print '<unfinished>'
    print '<nf>nf</nf>'
    if b['My Review']:
      print
      print b['My Review']
    print


with open('/Users/ryan/etc/goodreads_export_2015-04-02.csv') as f:
  books = list(b for b in csv.DictReader(f) if b)

  # to read
  render(sorted((b for b in books if b['Exclusive Shelf'] == 'to-read'),
                key=lambda b: b['Date Added'],
                reverse=True))

  # read
  render(sorted((b for b in books if b['Exclusive Shelf'] != 'to-read'
                   and (b['Date Read'] > '2013/04/21' or
                        b['Exclusive Shelf'] == 'didn-t-finish')),
                key=lambda b: b['Date Read'] or b['Date Added'],
                reverse=True))
