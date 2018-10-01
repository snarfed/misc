#!/usr/bin/env python3
"""Parses SFUSD school bus schedule PDFs and writes them to a CSV.

Requires PyPDF2 and fastkml.

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
import re
import string
import sys

# from fastkml import kml
# from pygeoif import geometry
# from shapely.geometry import Point, LineString, Polygon
import PyPDF2

SCHOOL = re.compile(r""" \ *
  School\ Transportation\ Schedule  \ +
  Effective\ Date\ + (?P<effective>\d+/\d+/\d+)  \ +
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
    # parse PDF
    with open('Lakeshore ES.pdf', 'rb') as pdf:
        reader = PyPDF2.PdfFileReader(pdf)
        text = '  '.join(reader.getPage(i).extractText()
                     for i in range(reader.numPages))

    school = SCHOOL.match(text)
    name = string.capwords(school['school'].strip().replace('Route', '').strip())
    print(name)

    routes = []
    for route in ROUTE.finditer(text, school.end()):
        route_data = route.groupdict()
        routes.append(route_data)
        route_data['days'] = route_data['days'].replace(' ', '')
        route_data['stops'] = []
        print('Route')
        print(route_data)

        for stop in STOP.finditer(text, route.end()):
            stop_data = stop.groupdict()
            route_data['stops'].append(stop_data)
            print('Stop')
            stop_data['street'] = stop_data['street'].strip()
            print(stop_data)
            if stop_data['street'].endswith('Route:'):
                stop_data['street'] = stop_data['street'].replace('Route:', '').strip()
                break

    # # generate KML
    # STATE: KML can't do street addresses? GPX probably not either?

    # root = kml.KML()
    # ns = '{http://www.opengis.net/kml/2.2}'
    # desc = 'SFUSD school bus routes 2018-19'
    # doc = kml.Document(ns, 'sfusd-school-buses-2018-doc', desc, desc)
    # root.append(d)

    # # Create a Placemark with a simple polygon geometry and add it to the doc
    # for stop in stops:
    #     pm = kml.Placemark(ns, '', 'name', 'description')
    # p.geometry =  Polygon([(0, 0, 0), (1, 1, 0), (1, 0, 1)])
    # f2.append(p)


if __name__ == '__main__':
    main(sys.argv[1:])
