#!/bin/bash
#
# This script converts a bday people file (usually ~/.bday/people) to a remind
# script. It reads the people file from stdin, and writes the remind script to
# stdout. For example, this bday people line:
#
#  Name:Ryan Barrett:Birthday:0000-01-01:
#
# will be converted to this remind script line:
#
#  1 Jan Ryan Barrett
#
# (note that REM and MSG are implicit.)
#
#
# Usage: bday2remind.sh < people_file > remind_script_file
#
# bday can be found at:    http://www.netmeister.org/apps/bday/
# remind can be found at:  roaringpenguin.com/penguin/open_source_remind.php

unset noclobber

NAME_FILE=`mktemp -ut bday2remind_names.XXXXXX`
DATE_FILE=`mktemp -ut bday2remind_dates.XXXXXX`

# copy the input bday people file to both tmp files
tee $NAME_FILE $DATE_FILE > /dev/null

# extract the names
cat $NAME_FILE | cut -d: -f2  > $NAME_FILE

# extract the dates and convert to remind-ready date format
cut -d: -f4 $DATE_FILE \
  | cut -d- -f2- \
  | xargs -n 1 --replace=MONTHDAY date -d '1970-MONTHDAY'  +'%e %b' \
  > $DATE_FILE

# generate remind lines
paste -d' ' $DATE_FILE $NAME_FILE


rm -f $NAME_FILE $DATE_FILE
