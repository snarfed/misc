#!/bin/bash
#
# Makes thumbnails for each of the images named on the command line. Uses
# ImageMagick(1), specifically convert(1). The thumbnails are placed in the
# thumbs/ subdirectory; their filenames are the same as the original images.
#
# Usage: make_thumbs.sh [IMAGE...]

if [ $# == 0 -o "$1" == "-h" -o "$1" == "--help" ]; then
  echo Usage: make_thumbs.sh [IMAGE...]
  exit
fi

mkdir -p thumbs

for file in $*; do
  convert "$file" -resize 200x200 "thumbs/$file"
done
