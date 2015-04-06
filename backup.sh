#!/bin/bash
#
# Backup everything I care about to snarfed.
#
# Run by mac os x's launchd, config in org.snarfed.backup.plist. my ssh keys are
# in Keychain Access.app, so they're loaded automatically.

TARGET="ryancb@snarfed.org:~"

# --links means copy symlinks as symlinks. add --delete to delete files in dest
# that aren't in source. removed --checksum and -z because the rsync server on
# ambym was using too much CPU and getting killed. :/
#
# tried --rsync-path 'nice rsync' and --rsync-path /home/ryanb/bin/nice_rsync.sh
# but neither worked.
BACKUP="nice rsync --archive -v --partial --one-file-system $@ -e ssh"

cd ~

# note that a / suffix on a source dir means copy the *contents* of the dir
# into the target dir; if the / suffix is missing, it means copy the dir itself
# into the target dir, recursively. (rsync is recursive by default.)

$BACKUP --relative --delete \
  --exclude={Cache\*/,lock,{places,urlclassifier3}.sqlite,\
/docs/{android,cpp_tutorial,django,elisp,emacs_manual,google-appengine,java,mysql\*,php,python\*}/,\
/etc/mail/,.git/,.svn/} \
  bin books docs .emacs.d etc .gnupg .*history .ssh \
  Library/{'Application Support'/{'Adium 2.0',Firefox},Keychains,PreferencePanes,Preferences} \
  $TARGET/laptop_backup

$BACKUP ./www/w/wp-content/gallery/ $TARGET/public_html/w/wp-content/gallery

# don't sync podcasts any more because they get unhappy on the nexus 4. they
# rarely copy fully.
# no --delete!
# $BACKUP --remove-source-files ./podcasts/ $TARGET/podcasts

# *backwards* back up phone camera pictures from server to here.
$BACKUP --delete $TARGET/phone_backup/Camera/ ./camera
chown --silent ryan:staff ./camera/*
