#!/usr/local/bin/bash
#
# unixify.sh
# http://snarfed.org/unixify
# Copyright 2010 Ryan Barrett <unixify@ryanb.org>
#
# Cleans up file names and contents to make them more unix-like. Removes
# punctuation, converts upper case to lower case, optimizes images, and converts
# .doc to .txt. With the dry run flag, -n, just prints what would be done.
#
# test filename: x\ y\ ]z,\[\ \)J\(\ \&\ #\&.jPeG
# should result in: x_y_z_J_and_and.jpg

# parse args
while getopts "n" options; do
  case $options in
    n ) DRYRUN="-n";;
    * ) echo 'Usage: unixify.sh FILES...'
        exit 1;;
  esac
done

# getops updates OPTIND to point to the arg it stopped at. shift $@ to that point.
shift $((OPTIND-1))

for file in "$@"; do
  # clean filename. (careful with the quoting and line break continuations!)
  newfile=`rename -v $DRYRUN \
      "y/ /_/;
      s/[!?':\",\[\]()#]//g; "'
      s/&/and/g;
      y/A-Z/a-z/;
      s/\.\.\./_/g;
      s/_+/_/g;
      s/_(\.[^.]+$)/$1/;
      s/\.jpeg$/.jpg/' \
      "$file"`

  if [[ $DRYRUN != "" ]]; then
    if [[ $newfile != "" ]]; then
      echo $newfile
    fi
    continue
  fi

  if [[ $newfile =~ ' renamed as ' ]]; then
    file=${newfile/* renamed as /}
  fi

  if [[ $file =~ \.(gif|jpg|png)$ ]]; then
    # optimize image
    convert $file $file
  elif [[ $file =~ \.doc$ ]]; then
    # convert word doc to text
    antiword $file > `basename $file .doc`.txt
  fi

  if [[ `file -b $file` =~ text,.*with\ CRLF ]]; then
    # remove any carriage returns
    sed --in-place 's/\r//g' $file
  fi
done

