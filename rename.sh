#!/bin/bash
#
# An interactive script for renaming images. Displays each image given on the
# command line, then asks the user for a new filename. The file extension is
# preserved. Useful for post-processing pictures taken by digital camera, along
# with choose.sh and choose.py.
#
# Usage: rename.sh [IMAGE...]
#
# BUGS:
# - filenames with spaces aren't handled correctly
#

if [ $# == 0 -o "$1" == "-h" -o "$1" == "--help" ]; then
  echo Usage: rename.sh [IMAGE...]
  exit
fi

# ask user to rename each file
VIEWER_PID=""

for file in $*; do
  kill $VIEWER_PID &> /dev/null

  # set the title so that kludges.lua can tell ion where to put the window
  WIDTH=`identify -format '%W' "$file"`
  ZOOM=`expr 100 \* 630 / $WIDTH`
  xloadimage -shrink -zoom $ZOOM -title rename.sh "$file" &> /dev/null &
  VIEWER_PID=$!

  extension=`echo "$file" | sed 's/.*[.]//'`

  newname=""
  while true; do
    read -e -p "Rename `basename $file` to (blank for none)? " newname

    if [ "$newname" == "" ]; then
      continue 2  # to the next file
    fi

    newname="$newname"."$extension"
    if [ ! -f "$newname" ]; then
      break
    fi

    read -e -p "$newname already exists. Overwrite? " overwrite
    if [ "$overwrite" == "y" ]; then
      break
    fi
  done

  mv "$file" "$newname"
done

kill $VIEWER_PID &> /dev/null
