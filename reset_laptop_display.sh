#!/bin/bash
#
# Reruns xrandr, resets ion's layout file, and recreates emacs frames.
#
# If an extra monitor is connected over VGA, HDMI, or DisplayPort, set it up as
# 1920x1200 portrait, laptop on the left, extra monitor on the right.
#
# Also check out the display-update package (currently installed and running),
# which does a lot of other display reset and auto-config when
# plugging/unplugging monitors and docking stations:
# /usr/share/doc/display-update/README

MONITOR=`xrandr --current | grep -oE '(DP1|VGA1|HDMI1) connected' | cut -d' ' -f1`

if [[ $MONITOR == "" ]]; then
  EXTRA_XRANDR="--output DP1 --off --output VGA1 --off --output HDMI1 --off"
else
  EXTRA_XRANDR="--output $MONITOR --auto --right-of LVDS1 --rotate left"
fi

xrandr --verbose --output LVDS1 --auto --primary $EXTRA_XRANDR    

# reset home office ion setup for extra monitor. (ion wipes it if i shut down
# when the extra monitor isn't connected.)
cp -f ~/.ion3/default-session--0/saved_layout.lua.extra_monitor \
    ~/.ion3/default-session--0/saved_layout.lua

for fn in delete-all-x-frames make-my-frames; do
  emacsclient -d $DISPLAY --eval "($fn)"
done
