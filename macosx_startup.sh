#!/bin/bash
#
# A .login for Mac OS X. Inspired by:
# http://stackoverflow.com/questions/135688/setting-environment-variables-in-os-x/5444960#5444960
launchctl setenv PATH $HOME/bin:/opt/homebrew/opt/coreutils/libexec/gnubin:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/bin:`launchctl getenv PATH`

brew services start mysql

# Homebrew tries to start this automatically, but it's currently failing
# brew services start httpd

ssh-add ~/.ssh/id_rsa ~/.ssh/google_compute_engine

# macOS starts this automatically
# eval $(gpg-agent --daemon)

# Mac OS sets TMPDIR to something opaque like e.g.
# /var/folders/y_/7mgz0yqd3hlgg2drhqx4ggf80000gn/T/
# i originally used /tmp instead...but gave that up to get emacsclient working,
# since it uses OS X's original dir.
# setenv TMPDIR /tmp/
ln -sf $TMPDIR /tmp/tmp

# docker start sequoia
# docker exec -it sequoia bash

gcloud emulators firestore start --database-mode=datastore-mode --host-port=:8089 < /dev/null >& /tmp/datastore-emulator.log &
