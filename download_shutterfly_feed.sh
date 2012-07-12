#!/bin/bash
#
# download_shutterfly_feed.sh
# Copyright 2008 Ryan Barrett
#
# Downloads all of the pictures in a Shutterfly RSS feed. Just give it the
# feed URL, and it will pull down all of the full-size pictures.
#
# Usage: download_shutterfly_feed.sh RSS_FEED
#
# The script itself is dirt simple. If you're looking for something robust and
# full-featured, you probably want an RSS reader that supports enclosures or a
# dedicated web photo downloader instead. This is simpler, though, which I like.

curl $1 | \
 sed "y/</\n/" | \
 grep -o -e 'img .\+src="[^"]\+' | \
 sed 's/^img .\+src="//' | \
 sed 's/$/\?cdl=1/' | \
 xargs -n 1 curl -O
