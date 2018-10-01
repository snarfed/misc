#!/usr/bin/env python3
"""Parses SFUSD school bus schedule PDFs and writes them to a CSV.

Run in a directory with SFUSD bus schedule PDFs.

Requires PyPDF2: https://mstamy2.github.io/PyPDF2/

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

Google My Maps:
https://mymaps.google.com/
https://www.google.com/maps/d/u/0/edit?mid=1Lt-2JuuQjh_tJS2nFC8wDBSuU9nmCN0I

Import:
https://support.google.com/mymaps/answer/3024836
"""
import csv
import glob
import re
import string
import sys

import PyPDF2

SCHOOL = re.compile(r""" \ *
  School\ Transportation\ Schedule  \ +
  Effective\ Date\ + (?P<effective>\d+[/-]\d+[/-]\d+)  \ +
  (?P<school>[^:]+)
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
    for pdf in glob.glob('*.pdf'):
        tsv = pdf.replace('.pdf', '.tsv')
        print('Converting %s to %s.' % (pdf, tsv))

        with open(pdf, 'rb') as f:
            reader = PyPDF2.PdfFileReader(f)
            text = '  '.join(reader.getPage(i).extractText()
                             for i in range(reader.numPages))

        # extract header, school name, effective date
        school = SCHOOL.match(text)
        school_name = string.capwords(school['school'].strip().replace('Route', '').strip())

        # look for next route
        routes = []
        for route in ROUTE.finditer(text, school.end()):
            route_data = route.groupdict()
            routes.append(route_data)
            route_data['days'] = route_data['days'].strip().replace('R', 'Th')
            route_data['stops'] = []

            # extract stops
            for stop in STOP.finditer(text, route.end()):
                stop_data = stop.groupdict()
                route_data['stops'].append(stop_data)
                stop_data['street'] = stop_data['street'].strip()
                if stop_data['street'].endswith('Route:'):
                    stop_data['street'] = stop_data['street'].replace('Route:', '').strip()
                    break

        # write out TSV
        with open(tsv, 'w', newline='') as f:
            writer = csv.writer(f, dialect=csv.excel_tab)
            writer.writerow(('School', 'Route', 'Bus', 'Run', 'Days', 'Stop Number',
                             'Stop Name', 'Address', 'Time'))
            for route in routes:
                for stop in route.get('stops', []):
                    writer.writerow((
                        school_name,
                        route['name'],
                        route['bus'],
                        route['run'],
                        route['days'],
                        stop['num'],
                        stop['name'],
                        '%s %s' % (stop['street_num'], stop['street']),
                        stop['time'],
                    ))


if __name__ == '__main__':
    main(sys.argv[1:])
