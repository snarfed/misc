"""Removes non-meaningful newlines from Markdown files.

Used to help port from the WordPress Markdown Extra plugin, where newlines
aren't meaningful, to Jetpack's Markdown implementation, where they are.

Overwrites files in place. Use with care!

Usage: strip_markdown_newlines.py [FILE...]

http://michelf.com/projects/php-markdown/
https://jetpack.com/support/markdown/
"""
import re
import sys

BLACKLIST = (
  'pubkey.txt',
)
CONTINUED_LINE = re.compile(r"""
  ^([][a-zA-Z()$%{}_`~+=/\%'"] |
    [0-9]+[^.] |
    [*-][^ ])
  """, re.VERBOSE | re.UNICODE | re.IGNORECASE)
HTML_TAG_START = re.compile(r"""
  <(style|script)[^<>]*> |
  <[^>]+$
  """, re.VERBOSE | re.UNICODE | re.IGNORECASE)
HTML_TAG_STOP = re.compile(r"""
  </(style|script)> |
  [^<]*>$
  """, re.VERBOSE | re.UNICODE | re.IGNORECASE)


for filename in sys.argv[1:]:
  if filename.split('/')[-1] in BLACKLIST:
    continue

  with open(filename) as input:
    contents = input.read()

  with open(filename, 'w') as output:
    lines = contents.splitlines()
    line = lines[0]
    output.write(line)

    started_code = in_code = in_html = False

    for next_line in lines[1:]:
      stripped = next_line.strip()
      if not in_code and stripped.startswith('```'):
        started_code = in_code = True
      else:
        started_code = False
      if not in_html:
        in_html = HTML_TAG_START.match(stripped)

      if (line and not in_code and not in_html and
          not line.endswith('  ') and not line.endswith('>') and
          not line.startswith('#') and
          CONTINUED_LINE.search(stripped)):
        output.write(' ')
        output.write(next_line.lstrip())
      else:
        output.write('\n')
        output.write(next_line)

      if stripped.startswith('```') and not in_code and not started_code:
        in_code = False
      if in_html and HTML_TAG_STOP.match(line.strip()):
        in_html = False

      line = next_line

    output.write('\n')
