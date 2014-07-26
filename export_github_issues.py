#!/usr/bin/python
"""Exports a GitHub repo's issues (with comments) as JSON inside a zip file.

Usage: export_github_issues.py USER/REPO OAUTH_TOKEN
"""

import json
import re
import sys
import urllib2
import zipfile


usage = 'Usage: %s USER/REPO OAUTH_TOKEN' % sys.argv[0]
assert len(sys.argv) == 3, usage
repo, token = sys.argv[1:3]

filename = '%s_%s_issues.zip' % tuple(repo.split('/'))
print 'Opening %s' % filename
zip = zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED)

def read(url):
  resp = urllib2.urlopen(urllib2.Request(
      url, headers={'Authorization': 'token ' + token}))
  data = json.loads(resp.read())
  sys.stdout.write('.'); sys.stdout.flush()
  # handle pagination.
  # https://developer.github.com/v3/#pagination
  for link in resp.headers.get('Link', '').split(','):
    match = re.match('<(.+)>; rel="next"', link)
    if match:
      data += read(match.group(1))
  return data

print 'Loading issues.',
# https://developer.github.com/v3/issues/#list-issues-for-a-repository
issues = read('https://api.github.com/repos/%s/issues?state=all' % repo)
zip.writestr('issues.json', json.dumps(issues, indent=2))
print '\nLoaded %d issues.\nFetching comments.' % len(issues),; sys.stdout.flush()

for issue in issues:
  num_comments = issue.get('comments', 0)
  if num_comments > 0:
    url = issue.get('comments_url')
    num = issue['number']
    if url:
      comments = read(url)
      zip.writestr('%d_comments.json' % num, json.dumps(comments, indent=2))
    else:
      print '\n#%d has %d comments but no comments_url!' % (num, num_comments)

zip.close()
print '\nDone.'
