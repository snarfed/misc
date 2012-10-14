#!/bin/bash

# use the existing ssh-agent
eval `head -n 2 ~ryanb/.ssh-agent.bash`

umask u+rw,og+
SOURCE=snarfed.org
TARGET=/home/ryanb/server_backup
BACKUP="rsync -e ssh -rtq --links --one-file-system --delete --bwlimit=1000"

# backup everything except laptop_backup and svn repo, it needs special treatment
$BACKUP $SOURCE:~/ --exclude={repo,laptop_backup}/ $TARGET

# backup svn repo - copy the current file first, and don't copy transactions
$BACKUP $SOURCE:~/repo/db/current $TARGET/repo/db
$BACKUP --exclude transactions/ --exclude db/current $SOURCE:~/repo $TARGET

chmod -R og-rwx $TARGET
