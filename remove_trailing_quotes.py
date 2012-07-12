#!/usr/bin/python
#
# takes a filename as the first positional argument:
#
#   ./remove_trailing_quotes.py /tmp/my_email.txt
#
# use as an editor with ViewSourceWith (firefox extension)

# TODO: don't remove whole trailing quotes. match this regex:
#   ^[ >]*On .+, .+ wrote:$
# TODO: leave just one blank line before sig

import sys

assert len(sys.argv) == 2

f = open(sys.argv[1], 'r+')
lines = f.readlines()

first = last = None
for i, line in enumerate(lines):
  line = line.strip()
  if not line:
    continue
  elif line[0] == '>':
    last = i
    if first is None:
      first = i
  elif line == '--':
    break
  else:
    first = last = None

if first is not None:
  assert last is not None
  del lines[first:last + 1]
  
  f.seek(0)
  f.truncate()
  f.writelines(lines)

f.close()
