#!/usr/bin/env python3
"""Unit tests for sfusd_buses.py. Based on the 2018-19 bus schedule PDFs.
"""
import unittest
from sfusd_buses import parse

INPUT = """\
   School Transportation Schedule   Effective Date 08/20/2018   KING ELEM  \
\
Route: KST1A       Bus: 606  Run: 1    Day: M T W R F     \
Stop_Number  Time     Stop_Name                 Stop_Address   \
7367         7:20 AM  1ST BUS STOP              AVE B  @ 12TH ST SE  SF     \
7368         7:25 AM  GATEVIEW                         REEVE/MARINER        \
7204         7:27 AM  BUS STOP GATEVIEW         &      NO PT/ SO INT  SF    \
7700         7:30 AM  E/B GATEVIEW @ 13TH ST    EB     GATEVIEW @ 13TH ST   \
449          7:55 AM  CARMICHAEL ELEM           N/B    7TH ST.@CLEVELAND    \
452          8:00 AM  BESSIE CARMICHAEL MIDDLE  824    HARRISON ST SF       \
7019         8:12 AM  FLYNN LZ                  SB     HARRISON ST  SF      \
7742         8:19 AM  SHOTWELL ST               &      23RD ST  SF          \
838          8:30 AM  KING ELEM                 S/B    WISCONSIN @ CORAL   \
\
Route: KST1P       Bus: 604  Run: 8    Day: R     \
Stop_Number  Time     Stop_Name                 Stop_Address   \
838          2:45 PM  KING ELEM                 S/B    WISCONSIN @ CORAL    \
7368         3:27 PM  GATEVIEW                         REEVE/MARINER        \
7718         3:40 PM  TI GYM/YMCA               749    9TH TREASURE ISLAN  \
\
School Transportation Schedule   Effective Date 08/20/2018   ANOTHER SCHOOL  \
\
Route: KST2P       Bus: 610  Run: 8    Day: M T W F     \
Stop_Number  Time     Stop_Name                 Stop_Address   \
838          2:45 PM  KING ELEM                 S/B    WISCONSIN @ CORAL    \
"""
ROUTES = [{
    'school': 'King Elem',
    'name': 'KST1A',
    'bus': '606',
    'run': '1',
    'days': 'M T W Th F',
    'stops': [dict(zip(('num', 'time', 'name', 'address'), vals)) for vals in (
        ('7367', '7:20 AM', '1st Bus Stop', 'Ave B @ 12th St SE SF'),
        ('7368', '7:25 AM', 'Gateview', 'Reeve/Mariner'),
        ('7204', '7:27 AM', 'Bus Stop Gateview', 'Bus Stop Gateview & No Pt/ So Int SF'),
        ('7700', '7:30 AM', 'E/B Gateview @ 13th St', 'EB Gateview @ 13th St'),
        ('449',  '7:55 AM', 'Carmichael Elem', 'N/B 7th St. @ Cleveland'),
        ('452',  '8:00 AM', 'Bessie Carmichael Middle', '824 Harrison St SF'),
        ('7019', '8:12 AM', 'Flynn LZ', 'SB Harrison St SF'),
        ('7742', '8:19 AM', 'Shotwell St', 'Shotwell St & 23rd St SF'),
        ('838',  '8:30 AM', 'King Elem', 'S/B Wisconsin @ Coral'),
    )],
}, {
    'school': 'King Elem',
    'name': 'KST1P',
    'bus': '604',
    'run': '8',
    'days': 'Th',
    'stops': [dict(zip(('num', 'time', 'name', 'address'), vals)) for vals in (
        ('838',  '2:45 PM', 'King Elem', 'S/B Wisconsin @ Coral'),
        ('7368', '3:27 PM', 'Gateview', 'Reeve/Mariner'),
        ('7718', '3:40 PM', 'TI Gym/YMCA', '749 9th Treasure Islan'),
    )],
}, {
    'school': 'Another School',
    'name': 'KST2P',
    'bus': '610',
    'run': '8',
    'days': 'M T W F',
    'stops': [dict(zip(('num', 'time', 'name', 'address'), vals)) for vals in (
        ('838',  '2:45 PM', 'King Elem', 'S/B Wisconsin @ Coral'),
    )],
}]


class ParseTest(unittest.TestCase):

    maxDiff = None

    def test_all(self):
        self.assertEqual(ROUTES, parse(INPUT))


if __name__ == '__main__':
    unittest.main()
