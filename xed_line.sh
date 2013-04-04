#!/bin/bash
#
# Taken from here, with the applescript tweaked:
# https://github.com/fpillet/NSLogger/issues/30#issuecomment-4839813
# More background:
# http://stackoverflow.com/questions/7957016/jump-to-file-and-line-from-outside-xcode-4-2
# http://openradar.appspot.com/radar?id=1480404

if [ "$1" = "-l" ] || [ "$1" = "--line" ] ; then
  line=$2
  file=$3
else
  line=1
  file=$1
fi

xed "$file"

osascript <<EOF
tell application "Xcode"
  activate
  tell application "System Events"
    tell process "Xcode"
      -- this menu item is dynamic, it's "Jump in 'FILENAME'...", so i can't use its
      -- name directly. i also can't use the Command-L key binding because i use it
      -- in my window manager (Slate).
      click menu item index 36 of menu "Navigate" of menu bar item "Navigate" of menu bar 1
      repeat until window "Jump" exists
      end repeat
      click text field 1 of window "Jump"
      set value of text field 1 of window "Jump" to "$line"
      keystroke return
    end tell
  end tell
end tell
EOF
