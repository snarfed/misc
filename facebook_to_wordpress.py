#!/usr/bin/python
"""Publishes a JSON collection of Facebook posts to WordPress via XML-RPC.

http://snarfed.org/facebook_to_wordpress

Reads one or more Facebook posts from stdin, in Graph API JSON representation,
and publishes them to a WordPress blog via XML-RPC. Includes attached images,
locations, links, people, and comments.

This script is in the public domain.

TODO:
mention.json
photo_location_comments.json
"""

__author__ = 'Ryan Barrett <public@ryanb.org>'

import datetime
import logging
import json
import os.path
import re
import sys
import time
import urllib2
import urlparse

import wordpress


# Only publish these post types.
POST_TYPES = ('link', 'checkin', 'photo', 'video')  # , 'status'

# Only publish these status types.
STATUS_TYPES = ('shared_story', 'added_photos', 'mobile_status_update')
  # 'wall_post', 'approved_friend', 'created_note', 'tagged_in_photo', 

# Don't publish posts from these applications
APPLICATION_BLACKLIST = ('Likes', 'Links', 'twitterfeed')

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
  wp = wordpress.XmlRpc(url, 0, user, passwd)

  for post in posts:
    # WP doesn't like it when you post too fast
    time.sleep(1)

    date = None
    if 'created_time' in post:
      date = parse_created_time(post['created_time'])

    content = post.get('message', '')
    phrase = re.search('^[^,.:;?!]+', content)
    # use the first phrase of the post as the title
    title = phrase.group() if phrase else date.date().isoformat()

    ptype = post.get('type')
    stype = post.get('status_type')
    app = post.get('application', {}).get('name')
    if ((ptype not in POST_TYPES and stype not in STATUS_TYPES) or
        (app and app in APPLICATION_BLACKLIST)):
      logging.info('Skipping %s' % title)
      continue

    # photo
    picture = post.get('picture', '')
    if ptype == 'photo' and stype == 'added_photos' and picture.endswith('_s.jpg'):
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

    # location
    place = post.get('place')
    if place:
      content += """
<p class="fb-checkin">at <a href="http://facebook.com/profile.php?id=%s">%s</a></p>
"""% (place['id'], place['name'])

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
      })

    for comment in post.get('comments', {}).get('data', []):
      # WP doesn't like it when you post too fast
      time.sleep(1)

      author = comment.get('from', {})
      content = comment.get('message')
      if not content:
        continue
      logging.info('Publishing comment "%s"', content[:30])

      post_url = 'https://www.facebook.com/permalink.php?story_fbid=%s&id=%s' % (
        comment.get('object_id'), post.get('from', {}).get('id'))
      content += ('\n<cite><a href="%s">via Facebook</a></cite>' % post_url)

      comment_id = wp.new_comment(post_id, {
            'author': author.get('name', 'Anonymous'),
            'author_url': 'http://www.facebook.com/profile.php?id=' + author.get('id'),
            'content': content,
            })

      if 'created_time' in comment:
        time.sleep(1)
        date = parse_created_time(comment['created_time'])
        logging.info("Updating comment's time to %s", date)
        wp.edit_comment(comment_id, {'date_created_gmt': date})

  print 'Done.'


def parse_created_time(iso8601):
  """Parses an ISO 8601 date/time string and returns a datetime object.
  """
  # example: 2012-07-23T05:54:49+0000
  # remove the time zone offset at the end, then parse
  return datetime.datetime.strptime(re.sub('[+-][0-9]{4}$', '', iso8601),
                                    '%Y-%m-%dT%H:%M:%S')


if __name__ == '__main__':
  main(sys.argv)
