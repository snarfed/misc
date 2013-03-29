#!/bin/bash
#
# Drop-in replacement for xed --line XXX FILE because xed itself is broken. This
# DOESN'T WORK yet though. it opens the file, then infinite loops. i suspect
# it's the 'repeat until window "Jump" exists".'
#
# Taken verbatim from:
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
                        keystroke "l" using command down
                        repeat until window "Jump" exists
                        end repeat
                        click text field 1 of window "Jump"
                        set value of text field 1 of window "Jump" to "$line"
                        keystroke return
                end tell
        end tell
end tell
EOF
