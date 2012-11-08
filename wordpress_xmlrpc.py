"""A minimal WordPress XML-RPC client library.

See http://codex.wordpress.org/XML-RPC_WordPress_API .

This library is in the public domain.
"""

__author__ = 'Ryan Barrett <public@ryanb.org>'

import xmlrpclib


class WordPress(object):
  """An XML-RPC interface to a WordPress blog.

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

  def __init__(self, xmlrpc_url, blog_id, username, password):
    self.proxy = xmlrpclib.ServerProxy(xmlrpc_url, allow_none=True,
                                       transport=WordPress.transport)
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

  def new_comment(self, post_id, author, author_url, comment):
    """Adds a new comment.

    Details: http://codex.wordpress.org/XML-RPC_WordPress_API/Comments#wp.newComment

    Args:
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
