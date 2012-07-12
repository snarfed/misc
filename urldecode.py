#!/usr/bin/python
import urllib, sys
print urllib.unquote(' '.join(sys.argv[1:]))
