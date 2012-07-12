#!/bin/bash
#
# Usage: get_imdb_link.sh [MOVIE TITLE]
#
# Runs an IMDB search for the given movie and prints out the URL of the first
# search result.

echo -n http://imdb.com
curl -L -s "http://www.imdb.com/find?s=tt&q=`echo $@ | tr ' ' +`" \
  | egrep -o '(Titles </b> \(Displaying [^)]+\)<table><tr> <td valign="top"><a href="([^"]+)"|<link rel="canonical" href="http://www.imdb.com/title/[^/]+/)' \
  | egrep -o '/title/[^"]+'
