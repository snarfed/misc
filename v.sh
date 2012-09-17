#!/bin/sh
# Shrink images to half of my screen width.
WIDTH=`identify -format '%W' $1`
ZOOM=`expr 100 \* 630 / $WIDTH`
xloadimage -zoom $ZOOM $@
