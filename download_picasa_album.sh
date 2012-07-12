#!/bin/bash
#
# download_picasa_album.sh
# Copyright 2007 Ryan Barrett
# http://snarfed.org/download_picasa_album
#
# Downloads all of the pictures in a Picasa Web album. Just give it the album's
# RSS feed, and it will pull down all of the full-size pictures.
#
# Usage: download_picasa_album.sh RSS_FEED
#
# The script itself is dirt simple. If you're looking for something robust and
# full-featured, you probably want an RSS reader that supports enclosures or a
# dedicated web photo downloader instead. This is simpler, though, which I like.

curl $1 | \
  sed "y/</\n/" | \
  grep -o -e "media:content url='[^']\+" | \
  sed "s/media:content url='//" | \
  xargs -n 1 curl -O
