#!/bin/bash
#
# A .login for Mac OS X. Inspired by:
# http://stackoverflow.com/questions/135688/setting-environment-variables-in-os-x/5444960#5444960
launchctl setenv PATH $HOME/bin:/usr/local/Cellar/coreutils/8.21/libexec/gnubin:/usr/local/bin:`launchctl getenv PATH`
