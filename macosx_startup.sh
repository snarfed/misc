#!/bin/bash
#
# A .login for Mac OS X. Inspired by:
# http://stackoverflow.com/questions/135688/setting-environment-variables-in-os-x/5444960#5444960
launchctl setenv PATH $HOME/bin:/usr/local/opt/coreutils/libexec/gnubin:/usr/local/bin:/usr/local/sbin:/usr/bin:`launchctl getenv PATH`

# this now happens automatically
sudo /usr/sbin/apachectl -k start

ssh-add ~/.ssh/id_rsa ~/.ssh/google_compute_engine ~/.ssh/ec2-keypair.pem ~/.ssh/azure-keypair.pem

eval $(gpg-agent --daemon)

# Mac OS sets TMPDIR to something opaque like e.g.
# /var/folders/y_/7mgz0yqd3hlgg2drhqx4ggf80000gn/T/
# i originally used /tmp instead...but gave that up to get emacsclient working,
# since it uses OS X's original dir.
# setenv TMPDIR /tmp/
ln -sf $TMPDIR /tmp/tmp

docker start sequoia
