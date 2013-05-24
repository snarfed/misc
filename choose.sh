#!/bin/bash
#
# An interactive script for choosing pictures to keep. Generates and opens an
# HTML page with thumbnails and a CGI form that posts to choose.py. Useful for
# post-processing pictures taken by digital camera, along with rename.sh.
#
# Usage: choose.sh [IMAGE...]
#
# BUGS:
# - filenames with spaces aren't handled correctly
#

if [ $# == 0 -o "$1" == "-h" -o "$1" == "--help" ]; then
  echo Usage: choose.sh [IMAGE...]
  exit
fi

# chooser page CGI script runs as www and needs to move files
chmod a+rwx .

# generate chooser page, and open it in an existing firefox window
THUMBFILE=`mktemp /tmp/choose.sh.html.XXXXXX`

cat << EOF >> $THUMBFILE
<html><body>
<form action='http://localhost/cgi-bin/choose.py'>
<input type="hidden" name="dir" value="$PWD">
EOF

for file in $*; do
  cat << EOF >> $THUMBFILE
<nobr>
<label for="$file"><a href='file://$PWD/$file'>
  <img src='file://$PWD/thumbs/$file'></a></label>
<input type="checkbox" id="$file" name="keep" value="$file" />
</nobr>
EOF
  # process the EXIF Orientation tag
  # more: ~/etc/find_jpeg_images_with_exif_orientation_rotated_on_ipad_iphone
  mogrify -auto-orient "$file"
done

cat << EOF >> $THUMBFILE
<br />
<input type='submit' value='Keep selected' />
</form></body></html>
EOF

`dirname $0`/make_thumbs.sh $* &

echo Loading thumbnail page file://$THUMBFILE in firefox...
open file://$THUMBFILE
