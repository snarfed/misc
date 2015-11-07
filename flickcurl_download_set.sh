#!/bin/bash
#
# Downloads all of the pictures in a flickr set
#
# NOT WORKING as of 5/26/2015. ~/bin/galdown.pl doesn't work either. :(
#
# Usage: flickcurl_download_set.sh [SET ID...]

ids=`flickcurl -q photosets.getPhotos "$@" | \
       grep -E -o 'ID [0-9]+' | cut -c4-`
for id in $ids; do
  wget `flickcurl -q photos.getSizes $id | \
          grep -E -o 'http://.+_o.jpg'`
done
