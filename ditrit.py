#!/usr/bin/python2
#
# ditrit.py
# Copyright 2006 Ryan Barrett <ditrit@ryanb.org>
# http://snarfed.org/ditrit
#
# See docstring for usage details.
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



USAGE = """A programmable application launcher. Reads input from stdin or
the X primary selection (aka clipboard), finds a template in the config file
that matches it, and runs the corresponding command. The input may be wholly
or partially inserted into the command string.

Options:
  -c <file>  Read config from file, not ~/.ditritrc
  -t         Don't actually run the command, just print it
  -X         Read input from the X primary selection (ie clipboard)
  -v         Display verbose debugging messages
  -V         Print version information and exit
  -h, --help Display this message

Web: http://snarfed.org/ditrit"""

import getopt
import os
import re
import string
import sys

# constants
VERSION = 'ditrit 0.1'

# default command-line options
CONFIG_FILE = None   # defaults to ~/.ditritrc in parse_args
TEST        = False
VERBOSE     = False
X_SELECTION = False


def main():
  templates = read_config()

  if X_SELECTION:
    input = get_x_selection()
  else:
    input = sys.stdin.read()

  input = input.strip()
  log('Read input "%s"' % input)
  
  for (template, cmd) in templates.items():
    match = re.search(template, input)
    if match:
      log('Matched template "%s" with command "%s"' % (template, cmd))
      cmd = match.expand(cmd).split()
      cmd_string = ' '.join(cmd)
      log('Expanded command to "%s"' % cmd_string)

      if TEST:
        print cmd_string
      else:
        os.spawnvp(os.P_NOWAIT, cmd[0], cmd)
      sys.exit(0)

  log('No matching template found.', error=True)
  sys.exit(1)


def read_config():
  """ Reads the config file from CONFIG_FILE. Returns a dictionary mapping
  template regexps to commands. Doesn't use ConfigParser because it splits
  at the first : or = it finds, and I need to allow those in templates.
  """
  log('Using config file %s' % CONFIG_FILE)

  templates = {}
  for (line, linenum) in zip(file(CONFIG_FILE), xrange(1, sys.maxint)):
    line = line.strip()
    if not line or line[0] == '#':
        continue

    # this regexp matches a line in the ditrit config file. e.g.:
    #
    #   Xtemplate regexpX  command  # optional comment
    #
    # where the delimiter X is any character (usually a double quote).
    #
    # \1 is the delimiter, \2 is the template, \3 is the command.
    #
    # this question marks means to match non-greedy, so that it stops at
    # the first delimiter it sees.
    #                         v
    match = re.match(r'^(.)(.+?)\1 ([^#]+)#?', line)
    if not match:
      log('Error in %s, line %d:\n%s' % (CONFIG_FILE, linenum, line),
          error=True)
      sys.exit(1)
    templates[match.group(2)] = match.group(3).strip()

  log('Read config:\n' + str(templates))
  return templates


def get_x_selection():
  import Xlib.display  # from the python X library, http://python-xlib.sf.net/
  import Xlib.X
  import Xlib.Xatom

  display = Xlib.display.Display()
  xsel_data_atom = display.intern_atom("XSEL_DATA")
  screen = display.screen()
  w = screen.root.create_window(0, 0, 2, 2, 0, screen.root_depth)
  w.convert_selection(Xlib.Xatom.PRIMARY,  # selection
                      Xlib.Xatom.STRING,   # target
                      xsel_data_atom,      # property
                      Xlib.X.CurrentTime)  # time

  while True:
    e = display.next_event()
    if e.type == Xlib.X.SelectionNotify:
      break

  assert e.property == xsel_data_atom
  assert e.target == Xlib.Xatom.STRING
  reply = w.get_full_property(xsel_data_atom, Xlib.X.AnyPropertyType)

  return reply.value


def parse_args(args):
  """ Parse command-line args. See doc comment for details.
  """
  global CONFIG_FILE, TEST, VERBOSE, X_SELECTION

  try:
    options, args = getopt.getopt(args, 'c:tXvVh', 'help')
  except getopt.GetoptError:
    type, value, traceback = sys.exc_info()
    log(value.msg, error=True)
    usage()
    sys.exit(2)

  for option, arg in options:
    if option == '-c':
      CONFIG_FILE = arg
    elif option == '-t':
      TEST = True
    elif option == '-X':
      X_SELECTION = True
    elif option == '-v':
      VERBOSE = True
    elif option == '-V':
      version()
      sys.exit(0)
    elif option in ('-h', '--help'):
      usage()
      sys.exit(0)

  if args:
    usage()
    sys.exit(2)

  if not CONFIG_FILE:
    CONFIG_FILE = os.path.join(os.getenv('HOME'), '.ditritrc')

  return args


def log(message, error=False):
  """ Overly simple logging facility. If anyone knows of a more fully
  featured logging facility that *ships with Python*, please let me know!
  """
  if error:
    print >> sys.stderr, message
  elif VERBOSE:
    print message

def usage():
  print USAGE

def version():
  print VERSION

if __name__ == '__main__':
  args = parse_args(sys.argv[1:])
  main()

