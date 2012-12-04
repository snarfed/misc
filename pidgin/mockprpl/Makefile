##
# mockprpl
# (formerly nullprpl)
#
# http://snarfed.org/space/gaim+mock+protocol+plugin
# Copyright (C) 2004-2007, Ryan Barrett <mockprpl@ryanb.org>
#
# Mockprpl on *nix requires Gaim 2.x and libtool 1.4 or higher. If the Gaim
# source is not installed in /usr/include or another standard location, add a
# -I clause to the $(LIBTOOL) compile command in the mockprpl rule.
#
# If you installed gaim from a binary package, you'll need the source! Install
# the gaim-dev package for your distro, or just download a tarball from
# http://gaim.sf.net.
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

VERSION = 0.3
PKGNAME = mockprpl-$(VERSION)

LIBTOOL = libtool
# -rpath <dir> tells libtool to build a shared library, and a static one if
# it wants, installable in <dir>.
LDFLAGS = -rpath /usr/lib/gaim -module -avoid-version
CXXFLAGS = -g -Wall -MD -MP -DHAVE_CONFIG_H
INCLUDES = `pkg-config --cflags --libs gtk+-2.0 gaim`
CXX = gcc $(CXXFLAGS) $(INCLUDES)

SRCS = mockprpl.c

default : mockprpl

mockprpl:
	$(LIBTOOL) --mode=compile $(CXX) -c -o $@.lo -MT $@.lo $(SRCS)
	$(LIBTOOL) --mode=link $(CXX) -o lib$@.la $(LDFLAGS) $@.lo

dist : clean
	ln -s . $(PKGNAME)
	tar cjhf $(PKGNAME).tar.bz2 --exclude $(PKGNAME).tar.bz2 --exclude .svn \
	  --exclude $(PKGNAME)/$(PKGNAME) $(PKGNAME)
	rm $(PKGNAME)

clean:
	rm -rf .libs/ *.o *.la *.lo *.so *.d
