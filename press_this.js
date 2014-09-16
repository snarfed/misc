// IndieWeb Press This bookmarklet tweaks. Use indieweb categories, set
// microformats2 classes on link and remove text.
// https://snarfed.org/indieweb-press-this-bookmarklets-for-wordpress

/* map type to mf2 class(es), wordpress category id, and content prefix */
var classes = {
  "like": "u-like u-like-of",
  "reply": "u-in-reply-to",
  "repost": "u-repost u-repost-of",
  "rsvp": "u-in-reply-to"
};
var categories = {
  "like": 27,
  "reply": 23,
  "repost": 28,
  "rsvp": 29
};
var content_prefixes = {
  "like": "likes ",
  "reply": "",
  "repost": "reposted ",
  "rsvp": "RSVPs <data class='p-rsvp' value='XXX'>XXX</data> to "
};

window.onload = function() {
  /* get 'type' query param. default to 'reply'. */
  var type = 'reply';
  var params = window.location.search.substr(1).split('&');
  for (var i = 0; i < params.length; i++) {
    var parts = params[i].split('=');
    if (parts[0] == 'type') {
      type = parts[1];
      break;
    }
  }

  var category = document.getElementById("in-category-" + categories[type]);
  if (category) {
    category.checked = true;
  }

  var elem = document.getElementById("title");
  title = elem.value;
  if (title.length > 60) {
    title = title.substr(0, 60) + "...";
  }

  var content = document.getElementById("content");
  var match = content.value.match("<a href='(.+)'>(.*)</a>\.");
  var prefix = content_prefixes[type] +
      "<a class='" + classes[type] + "' href='" + match[1] + "'>";
  var twitterPublish =
    '\n<a href="https://www.brid.gy/publish/twitter" class="u-bridgy-omit-link"></a>';
  var facebookPublish =
    '\n<a href="https://www.brid.gy/publish/facebook" class="u-bridgy-omit-link"></a>';

  if (match[1].startsWith("https://www.facebook.com/") ||
      match[1].startsWith("https://m.facebook.com/")) {
    /* Facebook. Add embed and Bridgy publish link. */
    if (type == 'rsvp') {
        content.value = prefix + 'this event</a>:';
    } else if (type == 'reply') {
        content.value = '\n' + prefix + '</a>';
    } else {
        content.value = prefix + 'this post</a>:';
    }
    content.value += '\n\
<div id="fb-root"></div> \n\
<script>(function(d, s, id) { \n\
  var js, fjs = d.getElementsByTagName(s)[0]; \n\
  if (d.getElementById(id)) return; \n\
  js = d.createElement(s); js.id = id; \n\
  js.src = "//connect.facebook.net/en_US/all.js#xfbml=1&appId=318683258228687"; \n\
  fjs.parentNode.insertBefore(js, fjs); \n\
}(document, "script", "facebook-jssdk"));</script> \n\
<div class="fb-post" data-href="' + match[1] + '"></div>' + facebookPublish;

  } else if (match[1].startsWith("https://twitter.com/") ||
             match[1].startsWith("https://mobile.twitter.com/")) {
    /* Twitter. Add embed and Bridgy publish link. */
    if (type == 'reply') {
        content.value = '\n' + prefix + '</a>';
    } else {
        content.value = prefix + 'this tweet</a>:';
    }
    content.value += '\n\
<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script> \n\
<blockquote class="twitter-tweet" lang="en" data-conversation="none" data-dnt="true"> \n\
<a href="' + match[1] + '"></a> \n\
</blockquote>' + twitterPublish;

  } else {
    /* Other post. Include title directly. */
    if (type == 'reply') {
      content.value = '\n' + prefix;
    }  else {
      content.value = prefix + (title ? match[2] : "this");
    }
    content.value += "</a>" + twitterPublish; // + facebookPublish;
  }

  content.focus();
  content.setSelectionRange(0, 0);
}

// Polyfill String.startsWith() since it's only supported in Firefox right now.
if (!String.prototype.startsWith) {
  Object.defineProperty(String.prototype, 'startsWith', {
    enumerable: false,
    configurable: false,
    writable: false,
    value: function (searchString, position) {
      position = position || 0;
      return this.indexOf(searchString, position) === position;
    }
  });
}
