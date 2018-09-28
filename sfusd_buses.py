#!/usr/bin/env python3
"""Parses SFUSD school bus schedule PDFs and writes them to a CSV.

Requires PyPDF2.

SFUSD bus schedule PDFs can be downloaded from:
https://www.sfusd.edu/en/transportation/school-bus-schedules.html

...specifically, from this public Google Drive folder:
https://drive.google.com/drive/u/0/folders/0B6SRbA2RjB6KcmNWWjF3QzBOY0E

Example text in a PDF:

School Transportation Schedule
Effective Date 08/20/2018
LAKESHORE ELEMENTARY

Route: LKS1A       Bus: 618  Run: 2    Day: M T W R F
Stop_Number  Time     Stop_Name    Stop_Address
7342  8:35 AM  HARTE LZ           300  SENECA AVE SF
7915  8:48 AM  WHITNEY YOUNG CTR  700  FONT  SF
7871  8:55 AM  DREW CC            E/B  EUCALYPTUS
...
"""
import re

import PyPDF2

SCHOOL = re.compile(r""" \ *
  School\ Transportation\ Schedule  \ +
  Effective\ Date\ + (?P<effective>\d+/\d+/\d+)  \ +
  (?P<school>[^:]+?)
""", re.VERBOSE)

ROUTE = re.compile(r"""
  Route:\ + (?P<name>\S+)  \ +
  Bus:\ +   (?P<bus>\d+)  \ +
  Run:\ +   (?P<run>\d+)  \ +
  Day:\ +   (?P<days>[MTWRF ]+)  \ +
  Stop_Number \ + Time \ + Stop_Name \ + Stop_Address
""", re.VERBOSE)

STOP = re.compile(r"""
  (?P<num>\d+)         \ +
  (?P<time>\d+:\d+\ [AP]M)  \ +
  (?P<name>.+?)        \ \ +
  (?P<street_num>[^ ]+)  \ \ +
  (?P<street>\D+)        \ +
""", re.VERBOSE)


def main(args):
    with open('Lakeshore ES.pdf', 'rb') as pdf:
        reader = PyPDF2.PdfFileReader(pdf)
        text = '  '.join(reader.getPage(i).extractText()
                     for i in range(reader.numPages))

        school = SCHOOL.match(text).groupdict()

        for route in ROUTE.finditer(text):
            route['days'] = route['days'].replace(' ', '')

        for stop in STOPS.finditer(text):
            stop['street'] = stop['street'].replace('Route:', '').strip()


if __name__ == '__main__':
    main(sys.argv[1:])
