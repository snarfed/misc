##
# gaim - Null Protocol Plugin
# http://snarfed.org/space/gaim+null+protocol+plugin
# Copyright (C) 2004, Ryan Barrett <nullprpl@ryanb.org>
#
# If the gaim source is not installed in /usr/local, change GAIMDIR to point to
# it. If you installed gaim from a binary package...duh, you'll need the
# source! You can get it at http://gaim.sf.net.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# GAIMDIR = /usr/local/include/gaim
GAIMDIR = $(HOME)/gaim-1.5.0/src

VERSION = 0.2
PKGNAME = nullprpl-$(VERSION)

LIBTOOL = libtool
LDFLAGS = -rpath /usr/local/lib/gaim -module -avoid-version
CXXFLAGS = -g -Wall -MD -MP -DHAVE_CONFIG_H
INCLUDES = -I$(GAIMDIR) `pkg-config --cflags --libs gtk+-2.0`
CXX = gcc $(CXXFLAGS) $(INCLUDES)

SRCS = nullprpl.c

default : nullprpl

nullprpl:
	$(LIBTOOL) --mode=compile $(CXX) -c -o $@.lo -MT $@.lo $(SRCS)
	$(LIBTOOL) --mode=link $(CXX) -o lib$@.la  $(LDFLAGS) $@.lo
	cp .libs/lib$@.so .

dist : clean
	ln -s . $(PKGNAME)
	tar cjhf $(PKGNAME).tar.bz2 --exclude $(PKGNAME).tar.bz2 --exclude .svn \
	  --exclude $(PKGNAME)/$(PKGNAME) $(PKGNAME)
	rm $(PKGNAME)

clean:
	rm -rf .libs/ *.o *.la *.lo *.so *.d
