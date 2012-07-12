#!/usr/bin/python
import urllib, sys
print urllib.quote(' '.join(sys.argv[1:]), ':')
