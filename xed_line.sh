#!/bin/bash
#
# Taken from here:
# https://github.com/PaulCapestany/NSLogger/commit/3cd09a1809f8a5d6af8be780970046f0623b119e

if [ "$1" = "-l" ] || [ "$1" = "--line" ] ; then
  line=$2
  file=$3
else
  line=1
  file=$1
fi

echo -n "${file##*/}:$line" | pbcopy

osascript <<EOF
tell application "Xcode"
  activate
  tell application "System Events"
    keystroke "o" using {command down, shift down}
    keystroke "v" using {command down}
    keystroke return
  end tell
end tell
EOF
