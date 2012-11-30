#!/usr/bin/python
"""Publishes a JSON collection of Facebook posts to WordPress via XML-RPC.

http://snarfed.org/facebook_to_wordpress

Reads one or more Facebook posts from stdin, in Graph API JSON representation,
and publishes them to a WordPress blog via XML-RPC. Includes attached images,
locations, links, people, and comments.

This script is in the public domain.

TODO:
- multiple picture upload. if you attach multiple pictures to an FB post,
this currently only uploads the first to WP.
"""

__author__ = 'Ryan Barrett <public@ryanb.org>'

import datetime
import itertools
import logging
import json
import os.path
import re
import sys
import time
import urllib2
import urlparse
import xmlrpclib


# Publish these post types.
POST_TYPES = ('link', 'checkin', 'video')  # , 'photo', 'status'

# Publish these status types.
STATUS_TYPES = ('shared_story', 'added_photos', 'mobile_status_update')
  # 'wall_post', 'approved_friend', 'created_note', 'tagged_in_photo', 

# Don't publish posts from these applications
APPLICATION_BLACKLIST = ('Likes', 'Links', 'twitterfeed')

# Attach these tags to the WordPress posts.
POST_TAGS = ['from-facebook']

# Uploaded photos are scaled to this width in pixels. They're also linked to
# the full size image.
SCALED_IMG_WIDTH = 500


def main(args):
  logging.getLogger().setLevel(logging.INFO)
  if len(args) != 4:
    print >> sys.stderr, \
        'Usage: facebook_to_wordpress.py XMLRPC_URL USERNAME PASSWORD < FILENAME'
    return 1

  logging.info('Reading posts from stdin')
  data = sys.stdin.read()
  posts = json.loads(data)['data']

  url, user, passwd = args[1:]
  logging.info('Connecting to %s as %s', *args[1:3])
  wp = wordpress.XmlRpc(url, 0, user, passwd, verbose=False)

  for post in posts:
    date = None
    if 'created_time' in post:
      date = parse_created_time(post['created_time'])

    content = post.get('message', '')
    first_phrase = re.search('^[^,.:;?!]+', content)

    ptype = post.get('type')
    stype = post.get('status_type')
    app = post.get('application', {}).get('name')
    if ((ptype not in POST_TYPES and stype not in STATUS_TYPES) or
        (app and app in APPLICATION_BLACKLIST) or
        # posts with 'story' aren't explicit posts. they're friend approvals or
        # likes or photo tags or comments on other people's posts.
        'story' in post):
      logging.info('Skipping %s' % title)
      continue

    # message (aka mention) tags
    tags = sum((tags for tags in post.get('message_tags', {}).values()), [])
    tags.sort(key=lambda x: x['offset'])
    if tags:
      last_end = 0
      orig = content
      content = ''
      for tag in tags:
        start = tag['offset']
        end = start + tag['length']

        content += orig[last_end:start]
        content += '<a class="fb-mention" href="http://facebook.com/profile.php?id=%s">%s</a>' % (
          tag['id'], orig[start:end])
        last_end = end

      content += orig[last_end:]

    # linkify embedded links
    content = linkify(content)

    # link
    link = post.get('link')
    if link and stype == 'shared_story':
      content += """
<table><tr><td>
  <a class="fb-link" href="%s"><img class="fb-link-thumbnail" src="%s" /></a>
</td><td>
  <a class="fb-link" href="%s"><span class="fb-link-name">%s</span></a><br />
""" % (link, picture, link, post.get('name', link))
      for elem in ('caption', 'description'):
        if elem in post:
          content += '<span class="fb-link-%s">%s</span><br />' % ((post[elem],) * 2)
      content += '</td></tr></table><br />'

    # tags (checkin, people, etc)
    content += '<p class="fb-tags">'

    # location
    place = post.get('place')
    if place:
      content += '<span class="fb-checkin"> at <a href="http://facebook.com/profile.php?id=%s">%s</a></span>' % (
        place['id'], place['name'])

    # with tags
    tags = post.get('with_tags', {}).get('data')
    if tags:
      content += '<span class="fb-with"> with '
      content += ', '.join('<a href="http://facebook.com/profile.php?id=%s">%s</a>' %
                           (tag['id'], tag['name']) for tag in tags)
      content += '</span>'

    content += '</p>'

    # photo
    picture = post.get('picture', '')
    if (ptype == 'photo' or stype == 'added_photos') and picture.endswith('_s.jpg'):
      orig_picture = picture[:-6] + '_o.jpg'
      logging.info('Downloading %s', orig_picture)
      resp = urllib2.urlopen(orig_picture)
      filename = os.path.basename(urlparse.urlparse(orig_picture).path)
      mime_type = resp.info().gettype()

      logging.info('Uploading as %s', mime_type)
      resp = wp.upload_file(filename, mime_type, resp.read())
      content += ("""
<p><a class="shutter" href="%(url)s">
  <img class="alignnone shadow" title="%(file)s" src="%(url)s" width='""" +
        str(SCALED_IMG_WIDTH) + """' />
</a></p>
""") % resp

    # "via Facebook"
    content += """<p class="fb-via">
<a href="http://facebook.com/permalink.php?id=%s&story_fbid=%s">via Facebook</a>
</p>""" % tuple(post['id'].split('_'))

    # title
    if first_phrase:
      title = first_phrase.group()
    elif place and 'name' in place:
      title = 'At ' + place['name']
    else:
      title = date.date().isoformat()

    # post!
    logging.info('Publishing %s', title)
    post_id = wp.new_post({
      'post_type': 'post',
      'post_status': 'publish',
      'post_title': title,
      # supposedly if you leave this unset, it defaults to the authenticated user
      # 'post_author': 0,
      'post_content': content,
      'post_date': date,
      'comment_status': 'open',
      # WP post tags are now implemented as taxonomies:
      # http://codex.wordpress.org/XML-RPC_WordPress_API/Categories_%26_Tags
      'terms_names': {'post_tag': POST_TAGS},
      })
    # WP doesn't like it when you post too fast
    time.sleep(1)

    for comment in post.get('comments', {}).get('data', []):
      author = comment.get('from', {})
      content = comment.get('message')
      if not content:
        continue
      logging.info('Publishing comment "%s"', content[:30])

      post_url = 'http://facebook.com/permalink.php?story_fbid=%s&id=%s' % (
        comment.get('object_id'), post.get('from', {}).get('id'))
      content += ('\n<cite><a href="%s">via Facebook</a></cite>' % post_url)

      comment_id = wp.new_comment(post_id, {
            'author': author.get('name', 'Anonymous'),
            'author_url': 'http://facebook.com/profile.php?id=' + author.get('id'),
            'content': content,
            })

      if 'created_time' in comment:
        time.sleep(1)
        date = parse_created_time(comment['created_time'])
        logging.info("Updating comment's time to %s", date)
        wp.edit_comment(comment_id, {'date_created_gmt': date})

      # WP doesn't like it when you post too fast
      time.sleep(1)

  print 'Done.'


def parse_created_time(iso8601):
  """Parses an ISO 8601 date/time string and returns a datetime object.
  """
  # example: 2012-07-23T05:54:49+0000
  # remove the time zone offset at the end, then parse
  return datetime.datetime.strptime(re.sub('[+-][0-9]{4}$', '', iso8601),
                                    '%Y-%m-%dT%H:%M:%S')

 
def linkify(text):
  """Adds HTML links to URLs in the given plain text.

  For example: linkify("Hello http://tornadoweb.org!") would return
  Hello <a href="http://tornadoweb.org">http://tornadoweb.org</a>!

  Ignores URLs starting with 'http://facebook.com/profile.php?id=' since they
  may have been added to "mention" tags in main().

  Based on https://github.com/silas/huck/blob/master/huck/utils.py#L59
  """
  # I originally used the regex from
  # http://daringfireball.net/2010/07/improved_regex_for_matching_urls
  # but it gets all exponential on certain patterns (such as too many trailing
  # dots), causing the regex matcher to never return. This regex should avoid
  # those problems.
  _URL_RE = re.compile(ur"""\b((?:([\w-]+):(/{1,3})|www[.])(?:(?:(?:[^\s&()]|&amp;|&quo
t;)*(?:[^!"#$%&'()*+,.:;<=>?@\[\]^`{|}~\s]))|(?:\((?:[^\s&()]|&amp;|&quot;)*\)))+)""")

  def make_link(m):
    url = m.group(1)
    if url.startswith('http://facebook.com/profile.php?id='):
      return url
    proto = m.group(2)
    href = m.group(1)
    if not proto:
      href = 'http://' + href
    return u'<a href="%s">%s</a>' % (href, url)
 
  return _URL_RE.sub(make_link, text)


class XmlRpc(object):
  """A minimal XML-RPC interface to a WordPress blog.

  Details: http://codex.wordpress.org/XML-RPC_WordPress_API

  TODO: error handling

  Class attributes:
    transport: Transport instance passed to ServerProxy()

  Attributes:
    proxy: xmlrpclib.ServerProxy
    blog_id: integer
    username: string, username for authentication, may be None
    password: string, username for authentication, may be None
  """

  transport = None

  def __init__(self, xmlrpc_url, blog_id, username, password, verbose=0):
    self.proxy = xmlrpclib.ServerProxy(xmlrpc_url, allow_none=True,
                                       transport=XmlRpc.transport, verbose=verbose)
    self.blog_id = blog_id
    self.username = username
    self.password = password

  def new_post(self, content):
    """Adds a new post.

    Details: http://codex.wordpress.org/XML-RPC_WordPress_API/Posts#wp.newPost

    Args:
      content: dict, see link above for fields

    Returns: string, the post id
    """
    return self.proxy.wp.newPost(self.blog_id, self.username, self.password,
                                 content)

  def new_comment(self, post_id, comment):
    """Adds a new comment.

    Details: http://codex.wordpress.org/XML-RPC_WordPress_API/Comments#wp.newComment

    Args:
      post_id: integer, post id
      comment: dict, see link above for fields

    Returns: integer, the comment id
    """
    # *don't* pass in username and password. if you do, that wordpress user's
    # name and url override the ones we provide in the xmlrpc call.
    #
    # also, use '' instead of None, even though we use allow_none=True. it
    # converts None to <nil />, which wordpress's xmlrpc server interprets as
    # "no parameter" instead of "blank parameter."
    #
    # note that this requires anonymous commenting to be turned on in wordpress
    # via the xmlrpc_allow_anonymous_comments filter.
    return self.proxy.wp.newComment(self.blog_id, '', '', post_id, comment)

  def edit_comment(self, comment_id, comment):
    """Edits an existing comment.

    Details: http://codex.wordpress.org/XML-RPC_WordPress_API/Comments#wp.editComment

    Args:
      comment_id: integer, comment id
      comment: dict, see link above for fields
    """
    return self.proxy.wp.editComment(self.blog_id, self.username, self.password,
                                     comment_id, comment)

  def upload_file(self, filename, mime_type, data):
    """Uploads a file.

    Details: http://codex.wordpress.org/XML-RPC_WordPress_API/Media#wp.uploadFile

    Args:
      filename: string
      mime_type: string
      data: string, the file contents (may be binary)
    """
    return self.proxy.wp.uploadFile(
      self.blog_id, self.username, self.password,
      {'name': filename, 'type': mime_type, 'bits': xmlrpclib.Binary(data)})
 

if __name__ == '__main__':
  main(sys.argv)
