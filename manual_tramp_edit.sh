#!/usr/local/bin/bash
#
# Used as $EDITOR in my TRAMP-based remote ssh shells in Emacs.

if which realpath >& /dev/null; then
  # FreeBSD
  path=`realpath $1`
else
  # Linux and other BSDs
  path=`readlink -f $1`
fi

echo 'Please edit file, then press enter:'
read -p "/ssh:$HOST:$path"

