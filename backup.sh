#!/bin/bash
#
# Backup everything I care about to snarfed.

# use the existing ssh-agent
eval `head -n 2 ~ryanb/.ssh-agent.bash`

TARGET="ryancb@snarfed.org:~"

# --links means copy symlinks as symlinks. add --delete to delete files in dest
# that aren't in source. removed --checksum and -z because the rsync server on
# ambym was using too much CPU and getting killed. :/
#
# tried --rsync-path 'nice rsync' and --rsync-path /home/ryanb/bin/nice_rsync.sh
# but neither worked.
BACKUP="nice rsync -rtq --links --one-file-system $@ --bwlimit=1000 -e ssh"
# PIPE="egrep -v '^rsync: failed to set times'"

cd ~ryanb

# note that a / suffix on a source dir means copy the *contents* of the dir
# into the target dir; if the / suffix is missing, it means copy the dir itself
# into the target dir, recursively. (rsync is recursive by default.)

$BACKUP --delete --exclude=\
{/.mozilla/firefox/{personal,work}/{Cache\*/,lock},\
/.adobe/,\
/.android/,\
/.cache/,\
/.config/,\
/.cpan/,\
/.emacs.d/backups/,\
/.git/,\
/.macromedia/,\
/.svn/,\
/android-sdk-linux/,\
/archive/,\
/camera/,\
/docs/{android,cpp_tutorial,django,elisp,emacs_manual,google-appengine,java,mysql\*,php,python\*}/,\
/etc/mail/,\
feedparser,\
/gae-samples/,\
/go/,\
/google_appengine/,\
/google-app-engine-samples/,\
/google-api-python-client/,\
/httplib2/,\
/logs/,\
/music/,\
{places,urlclassifier3}.sqlite,\
/podcasts/,\
/public_html/w/wp-content/gallery,\
/python-gflags/,\
/.ssh-agent\*,\
/server_backup/,\
/Steam/,\
/tal/,\
/vmware/,\
/webapp-improved/}\
  ./ $TARGET/laptop_backup

$BACKUP --delete ./public_html/w/wp-content/gallery/ $TARGET/public_html/w/wp-content/gallery 

# no --delete!
$BACKUP --remove-source-files ./podcasts/ $TARGET/podcasts

# *backwards* back up phone camera pictures from server to here.
$BACKUP --delete $TARGET/phone_backup/Camera/ ./camera
chown --silent ryanb:eng ./camera/*

unset noclobber
$BACKUP /etc/anacrontab $TARGET
