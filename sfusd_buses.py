#!/usr/bin/env python3
"""Parses SFUSD school bus schedule PDFs and writes them to a CSV.

Run in a directory with SFUSD bus schedule PDFs.

Requires PyPDF2: https://mstamy2.github.io/PyPDF2/

SFUSD bus schedule PDFs can be downloaded from:
https://www.sfusd.edu/en/transportation/school-bus-schedules.html

...specifically, from this public Google Drive folder:
https://drive.google.com/drive/u/0/folders/0B6SRbA2RjB6KcmNWWjF3QzBOY0E

See sfusd_buses_test.py for example text from a PDF.

Glossary of acronyms in the schedules:
* ES: elementary school
* MS: elementary school
* LZ: loading zone
* CC: community center?

Google My Maps:
https://mymaps.google.com/
https://www.google.com/maps/d/u/0/edit?mid=1Lt-2JuuQjh_tJS2nFC8wDBSuU9nmCN0I

How to import TSV files:
https://support.google.com/mymaps/answer/3024836

To see all addresses during development:
cut -f10 *.tsv | grep -v Address | sort | uniq
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
  (?P<school> .+? (?=Route:) )
""", re.VERBOSE)

ROUTE = re.compile(r"""
  Route:\ + (?P<name>\S+)  \ +
  Bus:\ +   (?P<bus>\d+)  \ +
  Run:\ +   (?P<run>\d+)  \ +
  Day:\ +   (?P<days>[MTWRF ]+)  \ +
  Stop_Number \ + Time \ + Stop_Name \ + Stop_Address
""", re.VERBOSE)

STOP = re.compile(r"""
  (?P<num>\d+)             \ +
  (?P<time>\d+:\d+\ [AP]M) \ +
  (?P<name>.+?)            \ \ +
  (?P<location>.+?          \ +
    (?= $ | Route: | School\ Transportation\ Schedule | \ \d{3,}\ ))
""", re.VERBOSE)


def main(args):
    for pdf in glob.glob('*.pdf'):
        tsv = pdf.replace('.pdf', '.tsv')
        print('Converting %s to %s.' % (pdf, tsv))

        with open(pdf, 'rb') as f:
            reader = PyPDF2.PdfFileReader(f)
            text = '  '.join(reader.getPage(i).extractText()
                             for i in range(reader.numPages))
            # print(text)

        routes = parse(text)

        # write out TSV
        with open(tsv, 'w', newline='') as f:
            writer = csv.writer(f, dialect=csv.excel_tab)
            writer.writerow((
                'School', 'Route', 'Bus', 'Run', 'Days',
                'Stop Name', 'Stop Number', 'Time', 'Location', 'Address'))
            for route in routes:
                for stop in route.get('stops', []):
                    writer.writerow((
                        route['school'],
                        route['name'],
                        route['bus'],
                        route['run'],
                        route['days'],
                        stop['name'],
                        stop['num'],
                        stop['time'],
                        stop['location'],
                        stop['address'],
                    ))


def clean(val):
    for sep in '@', '&':
        val = val.replace(sep, ' %s ' % sep)

    val = string.capwords(val)

    def capitalize(match):
        return match.group(1).capitalize()

    for pattern, repl in (
            (r' Es( |$)', ' Elementary '),
            (r' Ms( |$)', ' Middle '),
            (r'\b([NSEW]/?)b\b', r'\1B'),
            (r':sb( |$)', ' SB '),
            (r'([NS])e( |$)', r'\1E '),
            (r'([NS])w( |$)', r'\1W '),
            (r' [Bb]twn? (.+?) &( .*)?', r' & \1'),
            (r'S\.?f\.?', ''),
            (r'[Yy]mca', 'YMCA'),
            (r'(/[a-z])', capitalize),
            (r'[`]', ''),
            (r'/d$', ''),
            (r'S/?$', ''),
            (r'\($', ''),
    ):
        val = re.sub(pattern, repl, val)

    for pattern, repl in (
            ('Lz', 'LZ'),
            ('Ti', 'TI'),
            ('mariner', 'Mariner'),
            ('SE Or NE', ''),
            ('O farrell', "O'Farrell"),
            ("O'farrell", "O'Farrell"),
            ('Bucanan', 'Buchanan'),
    ):
        val = val.replace(pattern, repl)

    return re.sub(' +', ' ', val).strip()


def location_to_address(loc):
    addr = clean(loc)

    for pattern, repl in (
            (r'\b[NSEW]/?B\b', ''),
            (r'\b[NSns]/?[EWew]\b ([Cc]orner)?', ''),
            ('Bus Stop', ''),
            (r' C( |$)', r' Circle\1'),
            (r'Divis( |$)', r'Divisadero\1'),
            ('@', '&'),
            ('LZ', ''),
            (r'[-/]', ' & '),
            (r' \(pres\)', ''),
            (r'Bwtn 20 &', '& 20th'),
            ('0 Turk St', 'Jones & Turk'),
            (r'Reeve & Mariner', 'Gateview & Reeves'),
            (r'No Pt & +So Int', 'Northpoint'),
            ('Elem School', 'Elementary School'),
    ):
        addr = re.sub(pattern, repl, addr)

    return re.sub(' +', ' ', addr).strip()


def parse(text):
    """Parses text extracted from a bus schedule PDF.

    Args:
      text: str

    Returns:
      list of dict routes
    """
    routes = []

    # look for school
    for school_match in SCHOOL.finditer(text):
        school = clean(school_match['school'])

        # look for route
        for route_match in ROUTE.finditer(text, school_match.end()):
            route = route_match.groupdict()
            route.update({
                'school': school,
                'days': route['days'].strip().replace('R', 'Th'),
                'stops': [],
            })
            routes.append(route)

            # look for stops
            next = ''
            for stop_match in STOP.finditer(text, route_match.end()):
                stop = stop_match.groupdict()
                route['stops'].append(stop)

                name = clean(stop['name'])
                loc = clean(stop['location'])
                if loc.startswith('&') or loc.startswith('@'):
                    loc = '%s %s' % (name, loc)
                addr = location_to_address(loc)

                if ((name.split()[-1] in ('LZ', 'Elementary', 'Middle') or
                     name == school) and
                    ' & ' not in addr and not re.match(r'^\d+ ', addr)):
                    addr = '%s School, %s' % (name.replace(' LZ', ''), addr)

                stop.update({
                    'name': name,
                    'location': loc,
                    'address': addr,
                })

                next = text[stop_match.end():].lstrip()
                if next.startswith('Route:') or next.startswith('School '):
                    break

            if next.startswith('School '):
                break

    return routes


if __name__ == '__main__':

    main(sys.argv[1:])
