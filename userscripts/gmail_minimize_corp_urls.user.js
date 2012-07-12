// ==UserScript==
// @name           GMail Minimize Corp URLs
// @namespace      google
// @description    Shortens google corp URLs inside Gmail compose textareas by
// removing .corp.google.com and other unnecessary parts.
// @include        http*://mail.google.com/*
// ==/UserScript==

// Based on the Gmail Remove Trailing Quotes userscript.
//
// The regexes are duplicated in my .emacs file.
//
// DEPRECATED in favor of google3/experimental/fischman/url-corpinizer.
//
// TODO: get rid of the global vars and use an object that stores the textarea
// reference.

var minimize_corp_urls_textarea;
var minimize_corp_urls_last_value;

// in javascript regexps, use (?:...) as the "shy" grouping construct, ie
// it doesn't capture.
var minimize_corp_urls_regexes = [
  // dogfood groups (ie groups.google.com/a/google.com)
  [new RegExp("https?://g(roups)?"
   + "(\\.google\\.com/a/google\\.com/group|\\.corp\\.google\\.com)?/"
   + "([^/.\\s]+)"      // the group name
   + "(/browse_thread/thread/[^/?#\\s]+)?"  // the thread id
   + "([^\\s?#]*)?"     // the subthread id(s), if any
   + "(\\?[^\\s#]*)?"  // the query params, if any
   + "(#[^\\s]*)?", "g"),      // the fragment, if any
   "http://g/$3$4$7"], // *not* https, to avoid browser cert complaints
  // wiki.corp
  [new RegExp("https?://wiki"
   + "(\\.corp\\.google\\.com)?/"
   + "(twiki/bin/view/)?"
   + "([^\\s]+)", "g"),  // the page name and query params/fragment, if any
   "http://wiki/$3"],
  // buganizer
  // TODO: these don't work when the .corp.google.com is missing. why not?!?
  [new RegExp("https?://b(uganizer)?"
   + "(\\.corp\\.google\\.com)?/"
   + "(issue\\?id=)?"
   + "([0-9]+)"
   + "[^\\s]*", "g"),
   "http://b/$4"],
  // PDB
  [new RegExp("https?://p"
   + "(\\.corp\\.google\\.com)?"
   + "(:8443)?"
   + "/ProjectHandler\\?action=ViewProject(Detail)?&projectId="
   + "([0-9]+)", "g"),
   "http://p/?p=$4"],
  // mondrian
  [new RegExp("https?://(mondrian|cl)"
   + "(\\.corp\\.google\\.com)?/"
   + "changelist/"
   + "([0-9]+)"
   + "(\\?upload=ok)?", "g"),
   "http://cl/$3"],
  // GUTS
  [new RegExp("https?://remedyweb\\.corp\\.google\\.com/guts/ticket.php"
   + "\\?[^\\s]*"
   + "id=([0-9]+)"
   + "[^\\s]*", "g"),
   "http://tick/$1"],
  // generic *.corp.google.com
  [new RegExp("https?://"
   + "([^/.\\s]+)"
   + "\\.corp\\.google\\.com(/.*)", "g"),
   "http://$1$2"],
  // generic dogfood dasher apps (ie *.google.com/a/google.com)
  [new RegExp("https?://"
   + "([^/.\\s]+)"    // the app name
   + "(\\.google\\.com/a/google\\.com)?/"
   + "([^\\s]+)", "g"),    // the rest of the URL path
   "http://$1/$3"],  // *not* https, to avoid browser cert complaints
  // google code issue tracker issues
  [new RegExp("(http://code\\.google\\.com/p/"
   + "[^/\\s]+/"     // the project name
   + "issues/detail\\?id=[0-9]+"
   + ")[^\\s]*", "g"),
   "$1"]
];

function minimize_corp_urls() {
  var value = minimize_corp_urls_textarea.value;
  minimize_corp_urls_last_value = value;

  for (i in minimize_corp_urls_regexes) {
    value = value.replace(minimize_corp_urls_regexes[i][0],
                          minimize_corp_urls_regexes[i][1]);
  }

  minimize_corp_urls_textarea.value = value;
}

function minimize_corp_urls_undo() {
  if (minimize_corp_urls_last_value) {
    minimize_corp_urls_textarea.value = minimize_corp_urls_last_value;
  }
}

function minimize_corp_urls_on_load(event) {
  canvas_frame = document.getElementById("canvas_frame");
  if (canvas_frame) {
    canvas_doc = canvas_frame.contentDocument;
    canvas_doc.removeEventListener("DOMNodeInserted", minimize_corp_urls_node_inserted, false);
    canvas_doc.addEventListener("DOMNodeInserted", minimize_corp_urls_node_inserted, false);
  }
}

window.addEventListener("load", minimize_corp_urls_on_load, false);

function minimize_corp_urls_node_inserted(event) {
  textarea = canvas_doc.getElementsByClassName('Ak')[0];

  if (textarea) {
    minimize_corp_urls_textarea = textarea;
    minimize_corp_urls_last_value = null;

    textarea.removeEventListener("blur", minimize_corp_urls, false);
    textarea.addEventListener("blur", minimize_corp_urls, false);

    textarea.removeEventListener("focus", minimize_corp_urls_undo, false);
    textarea.addEventListener("focus", minimize_corp_urls_undo, false);
  }
}
