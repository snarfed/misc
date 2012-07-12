#!/bin/bash
#
# Ports pine patches from one version to the next. assumes the unmodified pine
# source for the new version has already been unpacked into ~/pine4.64
# (replace with the current version).
#
# Ryan Barrett <pine-info@ryanb.org>
# http:/snarfed.org/space/port_pine_patch
#
# Usage: port_pine_patch.sh PATCH_NAME NEW_PINE_VERSION"


if [ "$#" != "3" ]; then
  echo "Usage: port_pine_patch.sh PATCH_NAME OLD_PINE_VERSION NEW_PINE_VERSION"
  exit 0
fi

PATCH_NAME="$1"
OLD_VERSION="$2"
NEW_VERSION="$3"

PINE_SRC=~/pine$NEW_VERSION
PATCH_SRC=~/pine$NEW_VERSION-$PATCH_NAME
OLD_PATCH=~/src/pine/$PATCH_NAME.patch.$OLD_VERSION
NEW_PATCH=~/src/pine/$PATCH_NAME.patch.$NEW_VERSION


if [ -f $NEW_PATCH ]; then
  echo "$NEW_PATCH already exists; cowardly refusing to overwrite."
  exit 1
fi

if [ -d $PATCH_SRC ]; then
  echo "$PATCH_SRC already exists; assuming old patch is already applied."
else
  # set up a new codebase and apply the old patch
  cp -r $PINE_SRC $PATCH_SRC
  patch -d $PATCH_SRC -p 1 < $OLD_PATCH || exit 1  # this will often error out
fi

# build with the patch applied
cd $PATCH_SRC
./build lrh || exit 1

# clean out the new code base 
./build clean
rm -rf bin .bld.hlp pine.hlp.orig pine/date.c
find . -name \*.orig -or -name \*.rej | xargs rm -f

# generate a patch file for the new version and test it on a fresh codebase
cd `dirname $PATCH_SRC`
diff -rc `basename $PINE_SRC` `basename $PATCH_SRC` > $NEW_PATCH
if egrep "^Only in" $NEW_PATCH; then
  exit 1
fi

TEST_SRC=`mktemp -d "$PATCH_SRC"XXXXXX`
cp -r $PINE_SRC/* $TEST_SRC
patch --quiet -d $TEST_SRC -p 1 < $NEW_PATCH || exit 1  # this should succeed

# clean up, we're done!
rm -rf $TEST_SRC
echo "Success! New patch is $NEW_PATCH"
echo "Tkdiffing..."
tkdiff $OLD_PATCH $NEW_PATCH
#svn add $NEW_PATCH

