#!/bin/sh
#
# snipscrape
# http://snarfed.org/snipscrape
# Copyright 2004 Ryan Barrett <snipscrape@ryanb.org>
#
# File: snipscrape.sh
#
# This script preprocesses the input html, then passes it to xsltproc, which
# transforms it using snipscrape.xslt. It takes html pages as arguments. For
# more information, see snipscrape.xslt.
#
# Example usage:
#
# $ snipscrape.sh snip1.html snip2.html > snips.xml
#
# Snipscrape is only supported on SnipSnap 0.4.2, and has not been tested on
# other versions. It should work, but your mileage may vary.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA
#

XSLT_FILE=`dirname $0`/snipscrape.xslt
XSLTPROC_PARAMS="--html --novalid"

# check args
if [[ $# = "0" || $1 = "--help" ]]; then
  echo 'Usage: snipscrape.sh FILES...'
  exit 1
elif [ ! -e "$XSLT_FILE" ]; then
  echo "$XSLT_FILE not found. It should be in the same directory as:"
  echo "$0 ."
  exit 1
fi


# check that xsltproc can parse the input files successfuly
for FILE in $*; do
  if ! xsltproc $XSLTPROC_PARAMS --noout $XSLT_FILE "$FILE"; then
    exit $?
  fi
done


# now actually transform the input files
echo '<?xml version="1.0"?>'
echo '<snipspace>'

for FILE in $*; do
  # first escape {, [, |, and other chars, then transform the input file
  sed 's/{/\\\{/
       s/&#123;/\\{/
       s/\[/\\\[/
       s/&#91;/\\\[/
       s/|/\\|/
       s/&#95;&#95;/\\_\\_/
       s/&#104;/h/' "$FILE" | \
  xsltproc $XSLTPROC_PARAMS $XSLT_FILE -
done

echo '</snipspace>'
