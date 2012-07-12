#!/bin/bash
#
# An interactive script for rotating images 90 degrees clockwise. Displays each
# image given on the command line, then asks the user whether it should be
# rotated. Useful for post-processing pictures taken by digital camera.
#
# Usage: rotate.sh  [IMAGE...]
#
# BUG: when each xloadimage instance is killed, the shell prints a "Terminated
# ..." line to the terminal as part of job control. i haven't figured out how
# to suppress this yet.
#

if [ $# == 0 -o "$1" == "-h" -o "$1" == "--help" ]; then
  echo Usage: rotate.sh  [IMAGE...]
  exit
fi

# use a counter to loop through the files so we can go backward if needed
files=($*)
i=0
prev_reply=""

while (( $i < $# )); do
  file=${files[$i]}

  # process the EXIF Orientation tag
  # more: ~/etc/find_jpeg_images_with_exif_orientation_rotated_on_ipad_iphone
  mogrify -auto-orient "$file"

  # set the title so that kludges.lua can tell ion where to put the window
  WIDTH=`identify -format '%W' "$file"`
  ZOOM=`expr 100 \* 630 / $WIDTH`
  xloadimage -shrink -zoom $ZOOM -title rename.sh "$file" &> /dev/null &

#   if [ $? != 0 ]; then
#     echo Could not display $file, continuing to next image.
#     continue
#   fi

  VIEWER_PID=$!

  reply=""

  until [[ "$reply" == "y" || "$reply" == "n" || \
          ( "$reply" == "u" && "$prev_reply" != "" ) ]]; do
    # can only undo if we have the last command stored
    can_undo=""
    if [ "$prev_reply" != "" ]; then
      can_undo="/u"
    fi

    # read a single keystroke
    read -n 1 -p "Rotate `basename $file` (y/n$can_undo)? " reply
    echo
  done

   /bin/kill $VIEWER_PID &> /dev/null

  if [ "$reply" == "y" ]; then     # rotate
    convert "$file" -rotate 90 "$file" &

  elif [ "$reply" == "u" ]; then   # undo last rotation, if any
    (( i-- ))

    if [ "$prev_reply" == "y" ]; then
      file=${files[$i]}
      convert "$file" -rotate 270 "$file"
    fi

    prev_reply=""
    continue
  fi

  prev_reply=$reply
  (( i++ ))
done

