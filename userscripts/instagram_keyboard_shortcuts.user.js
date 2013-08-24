// ==UserScript==
// @name           Instagram Stream Keyboard Navigation
// @description    Adding key navigation to instagram's new online stream (J/K ./, right/left down/up) and highlights "current" photo
// @version        1.1.0
// @author         Pedro Gaspar & Matt Sephton
// @include        http://www.instagram.com/*
// @include        http://instagram.com/*
// ==/UserScript==

// a function that loads jQuery and calls a callback function when jQuery has finished loading
function addJQuery(callback) {
  var script = document.createElement("script");
  script.setAttribute("src", "//ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js");
  script.addEventListener('load', function() {
    var script = document.createElement("script");
    script.textContent = "window.jQ=jQuery.noConflict(true);jQ(document).ready(function() {(" + callback.toString() + ")()});";
    document.body.appendChild(script);
  }, false);
  document.body.appendChild(script);
}

// the guts of this userscript
function main() {
  // Note, jQ replaces $ to avoid conflicts.

  var curr = jQ(".timelineItem").first();
  var not_last = ":not(.timelineLast)";

  jQ(document).keydown(function(event) {
    if (!event)
      event = window.event;

    var code = event.keyCode ? event.keyCode : event.which;
    
    switch(code)
    {
      case 74: // J
      case 190: // .
        nextImage();
      break;
      
      case 75: // K
      case 188: // ,
        prevImage();
      break;
      
      case 76: // L
        likeImage();
      break;
      
      case 37: // left
      case 38: // up
        event.preventDefault();
        prevImage();
        return false;
      break;
      
      case 39: // right
      case 40: // down
        event.preventDefault();
        nextImage();
        return false;
      break;
      
      default:
        // alert("key code: "+ event.which);
      
      return true;
    }

    function likeImage() {
      jQ(curr).find('.timelineLikes a').trigger('click');
    }

    function nextImage() {
        jQ("body").scrollTop(curr.next(not_last).offset().top);
        jQ(curr).find('.timelineCard, .timelinePhoto::after').css({'border-color':'#C0C0C0', 'box-shadow': '0 1px 16px rgba(0, 0, 0, 0.1)'});
        curr = curr.next(not_last);
        jQ(curr).find('.timelineCard, .timelinePhoto::after').css({'border-color':'#808080', 'box-shadow': '0 1px 16px rgba(0, 0, 0, 0.5)'});
    }
    
    function prevImage() {
        jQ("body").scrollTop(curr.prev(not_last).offset().top);
        jQ(curr).find('.timelineCard, .timelinePhoto::after').css({'border-color':'#C0C0C0', 'box-shadow': '0 1px 16px rgba(0, 0, 0, 0.1)'});
        curr = curr.prev(not_last);
        jQ(curr).find('.timelineCard, .timelinePhoto::after').css({'border-color':'#808080', 'box-shadow': '0 1px 16px rgba(0, 0, 0, 0.5)'});
    }
  });
}

// load jQuery and execute the main function
addJQuery(main);
