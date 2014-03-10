// ==UserScript==
// @name         Let's Talk
// @namespace    h-card
// @description  Highlights, expands, and re-renders the contact info in an h-card.
// @include      *
// @require      https://raw.github.com/glennjones/microformat-shiv/master/microformat-shiv.min.js
// @resource     css lets_talk.user.css
// ==/UserScript==

// https://snarfed.org/lets_talk
// Ryan Barrett <public@ryanb.org>
//
// Highlights and standardizes the contact info in a microformats2 h-card on a
// personal web site. Expands it, renders the contact methods (p-facetime,
// p-tel, u-email, u-impp, u-url) with icons, hides the rest, and pins it to the
// upper left corner.
//
// More about microformats2 h-cards: http://microformats.org/wiki/h-card
//
// Uses the microformat-shiv library: http://microformatshiv.com/
//
// Changelog:
// 0.1 3/9/2013:
// - initial release

function lt_render() {
  var items = microformats.getItems({'filters': ['h-card']});
  // console.log(JSON.stringify(items));

  var props = items.items[0].properties;
  node = document.createElement('div');
  node.setAttribute('class', 'lt');

  var inner = '';
  if (props.url)
    inner += '<a class="u-url" href="' + props.url[0] + '"></a>';
  if (props.impp)
    inner += '<a class="u-impp" href="' + props.impp[0] + '"></a>';
  if (props.facetime)
    inner += '<a class="p-facetime" href="' + props.facetime[0] + '"></a>';
  if (props.tel)
    inner += '<a class="p-tel" href="' + props.tel[0] + '"></a>';
  if (props.email)
    inner += '<a class="u-email" href="' + props.email[0] + '"></a>';

  node.innerHTML = inner;
  document.body.appendChild(node);

  // add stylesheet using GreaseMonkey API
  GM_addStyle(GM_getResourceText('css'));
}

window.onload = lt_render();

