#!/usr/bin/python
"""Publishes a JSON collection of Facebook posts to WordPress via XML-RPC.

Reads one or more Facebook posts from stdin, in Graph API JSON representation,
and publishes them to a WordPress blog via XML-RPC. Includes attached images,
locations, links, people, and comments.

This script is in the public domain.

TODO:
with_tags
picture
place
"""

__author__ = 'Ryan Barrett <public@ryanb.org>'

import datetime
import json
import re
import sys
import time

import wordpress


# Only publish these post types.
POST_TYPES = ('link', 'checkin', 'photo', 'video')  # , 'status'

# Only publish these status types.
STATUS_TYPES = ('shared_story', 'added_photos', 'mobile_status_update')
  # 'wall_post', 'approved_friend', 'created_note', 'tagged_in_photo', 

# Don't publish posts from these applications
APPLICATION_BLACKLIST = ('Likes', 'Links', 'twitterfeed')

def main(args):
  if len(args) != 4:
    print >> sys.stderr, \
        'Usage: facebook_to_wordpress.py XMLRPC_URL USERNAME PASSWORD < FILENAME'
    return 1

  print 'Reading posts from stdin...'
  data = sys.stdin.read()
  posts = json.loads(data)['data']

  url, user, passwd = args[1:]
  print 'Connecting to %s as %s ...' % tuple(args[1:3])
  wp = wordpress.XmlRpc(url, 0, user, passwd)

  for post in posts:
    # WP doesn't like it when you post too fast
    # time.sleep(1)

    ptype = post.get('type')
    stype = post.get('status_type')
    app = post.get('application', {}).get('name')
    if ((ptype and ptype not in POST_TYPES) or
        (stype and stype not in STATUS_TYPES) or 
        (app and app in APPLICATION_BLACKLIST)):
      continue

    date = None
    if 'created_time' in post:
      date = parse_created_time(post['created_time'])

    # use the first phrase of the post as the title
    content = post.get('message', '')
    # if not content:
    #   # this is a like, friend approval, comment on someone else's
    #   # post, or something else that's not an explicit new post.
    #   continue

    phrase = re.search('^[^,.:;?!]+', content)
    title = phrase.group() if phrase else date.date().isoformat()

    print 'Publishing %s...' % title
    # post_id = wp.new_post({
    #   'post_type': 'post',
    #   'post_status': 'publish',
    #   'post_title': title,
    #   # leave blank for the connected user?
    #   # 'post_author': 0,
    #   'post_content': content,
    #   'post_date': date,
    #   'comment_status': 'open',
    #   })

    # TODO: for pictures, use 'picture' element. it will look like this:
    # https://fbcdn-photos-a.akamaihd.net/hphotos-ak-ash3/523628_10100417606190643_1013174541_s.jpg
    # just change the _s.jpg suffix to _o.jpg to get a full(ish) sized picture.

    for comment in post.get('comments', {}).get('data', []):
      # WP doesn't like it when you post too fast
      # time.sleep(1)

      author = comment.get('from', {})
      content = comment.get('message')
      if not content:
        continue
      print '  Publishing comment "%s..."' % content[:30]

      post_url = 'https://www.facebook.com/permalink.php?story_fbid=%s&id=%s' % (
        comment.get('object_id'), post.get('from', {}).get('id'))
      content += ('\n<cite><a href="%s">via Facebook</a></cite>' % post_url)

      # comment_id = wp.new_comment(post_id, {
      #       'author': author.get('name', 'Anonymous'),
      #       'author_url': 'http://www.facebook.com/profile.php?id=' + author.get('id'),
      #       'content': content,
      #       })

      # if 'created_time' in comment:
      #   date = parse_created_time(comment['created_time'])
      #   wp.edit_comment(comment_id, {'date_created_gmt': date})

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
