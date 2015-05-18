#!/bin/bash
#
# A .login for Mac OS X. Inspired by:
# http://stackoverflow.com/questions/135688/setting-environment-variables-in-os-x/5444960#5444960
launchctl setenv PATH $HOME/bin:/usr/local/Cellar/coreutils/8.23_1/libexec/gnubin:/usr/local/bin:/usr/bin:`launchctl getenv PATH`
# sudo /Library/StartupItems/VirtualBox/VirtualBox restart
sudo apachectl -k start
sudo pmset -a sleep 0

cd ~/color/color
source ~/color/color/setenv.sh
# https://github.com/ColorGenomics/color/wiki/Database-Runbook
clr pg:start
