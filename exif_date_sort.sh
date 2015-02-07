#!/bin/tcsh
#
# Usage: exif_date_sort.sh [FILE...]
#
# Sorts a list of image filenames by the date in their EXIF tags.
# Useful for collating pictures from multiple cameras in chronological order.
#
# Supports three date tags: DateTime, DateTimeOriginal, and DateTimeDigitized.
#
# TODO: also support GPSDate and/or GPSTime?
# TODO: support spaces in filenames

set container=`mktemp`

foreach f ($*)
  set tag=`exif -l $f | grep -m 1 -E 'Date and Time .*\*' | cut -d' ' -f1`
  echo "`exif -m -t $tag $f` $f" >> $container
end

sort $container |cut -d' ' -f3-
rm $container
