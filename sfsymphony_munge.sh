#!/bin/bash
#
# DEPRECATED!!! They now let you download a single ical file with all of your
# events from http://sfsymphony.org/account/ .
#
# Takes one or more San Francisco Symphony vCal links on sfsymphony.org (e.g.
# http://www.sfsymphony.org/CalendarItem.ashx?PerfNo=8723), fetches them,
# concatenates them, and munges them so that they can be imported into Google
# Calendar.
#
# Specifically, removes blank lines and VALARM sections, and adds a newline
# after END:VCALENDAR.
#
# Usage: sfsymphony_munge.sh [LINK ...]
#
# Requires curl(1) and grep(1).
#
# To do this for a whole season, log into your sfsymphony.org account, go to
# your account page (it sends you there automatically), then do:
#
# grep -Eo 'https://www.sfsymphony.org/CalendarItem.ashx\?PerfNo=[0-9]+' \
#   ~/San\ Francisco\ Symphony\ -\ MySFS.html \
#   | xargs ~/src/misc/sfsymphony_munge.sh > ~/symphony.ics

echo BEGIN:VCALENDAR

echo "$*" | \
  xargs -n 1 curl -L | \
  grep -v -e ':VCALENDAR$' | \
  grep -v -e '^$' | \
  grep -v -e '\(:VALARM$\|^TRIGGER:\|^ACTION:\|^DESCRIPTION:Reminder$\)'

echo END:VCALENDAR
