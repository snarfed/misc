#!/bin/bash -x
#
# Backup much of snarfed.org to my laptop.
#
# Run by mac os x's launchd, config in org.snarfed.backup.plist. my ssh keys are
# in Keychain Access.app, so they're loaded automatically.

umask u+rw,og+
SOURCE=ryancb@snarfed.org
TARGET=~/server_backup
BACKUP="rsync -e ssh -rtv --links --one-file-system --delete" # --bwlimit=1000"

$BACKUP $SOURCE:~/ --exclude={archive,laptop_backup,phone_backup,public_html/src,public_html/w/wp-content/{cache,gallery}}/ $TARGET

chmod -R og-rwx $TARGET
