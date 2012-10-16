#!/bin/bash
#
# download_smugmug_album.sh
# http://snarfed.org/download_smugmug_album
#
# Usage: download_smugmug_album.sh USERNAME ALBUM_ID
#
# Downloads the pictures in a Smugmug album. Give it the username and album ID,
# and it will pull down all of the full-size pictures. For example, in this URL:
#
# http://foo.smugmug.com/Bar/Baz/123456_XXyyZZ#!i=...
#
# the username is foo and the album ID is 123456_XXyyZZ.
#
# The script itself is dirt simple. If you're looking for something robust and
# full-featured, you probably want an RSS reader that supports enclosures or a
# dedicated web photo downloader instead. This is simpler, though, which I like.
#
# This script is in the public domain.
#
# Based on http://www.jwz.org/blog/2010/04/fuck-smugmug/#comment-4708 . Also see
# https://github.com/realityforge/housekeeping-scripts/blob/master/smugmug/smugget.sh

curl "http://$1.smugmug.com/hack/feed.mg?Type=gallery&Data=$2&format=rss200&Paging=0&ImageCount=9999" | \
  grep -o -E 'media:content url="(.+/i-[^-]+\.jpg)' | \
  sed 's/media:content url="//' | \
  xargs -n 1 curl -O
