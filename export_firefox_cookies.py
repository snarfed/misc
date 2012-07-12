#!/usr/bin/python

# This script can be used to export Firefox 3 cookies from the cookie
# database to a file containing the cookies in the Mozilla cookie file
# format for using the cookies in tools, that can read such files
#
# Written by Dirk Sohler and published under CC-by-sa
# See http://creativecommons.org/licenses/by-sa/3.0/
#
# There are all parts commented for learning purposes. You might want
# to remove this comments before using this code in your applications.
#
# Visit http://blog.schlunzen.org for my blog (German only)
#
# This is revision 1.1 of this script.
#
# NOTE: edited by ryan on 1/4/2009 to take input and output files as command
# line params, export all hosts instead of the one provided on the command
# line, and not report number of cookies.


# Importing the modules, that we need to connect to the database and to
# parse inputs from the system like parameters, etc.

import sqlite3 as db
import sys


# Defining the Files, we want to use. cookiedb is the cookie database
# file, and targetfile is the file in that we want to store the cookies
# in the Mozilla cookie file format

cookiedb = sys.argv[1]
targetfile = sys.argv[2]


# Here we create the connection and define the cursor. Using the cursor
# we'll have access to the database

connection = db.connect(cookiedb)
cursor = connection.cursor()


# This is the statement, it's usual SQL. I splitted the contents of the
# statement and the statement itself, because of aesthetic purposes :)

contents = "host, path, isSecure, expiry, name, value"
cursor.execute("SELECT " +contents+ " FROM moz_cookies")


# Here we open the target file for writing. Please note: Opening
# this file (and later closing it) WILL DESTROY all data, that was
# in this file before

file = open(targetfile, 'w')


# And FIRE! ... Here we parse the output (delivered by the cursor)
# to the Mozilla cookie file format and writing it to the target file

index = 0
for row in cursor.fetchall():
  file.write("%s\tTRUE\t%s\t%s\t%d\t%s\t%s\n" % (row[0], row[1],
             str(bool(row[2])).upper(), row[3], str(row[4]), str(row[5])))
  index += 1


# Now we want to close the file and the database connection

file.close()
connection.close()
