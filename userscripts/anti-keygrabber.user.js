// ==UserScript==
// @name anti key-grabber
// @description Prevent web apps from capturing and muting vital keyboard shortcuts
// @grant none
// @version 1.1
// ==/UserScript==
(function(){
var isMac = unsafeWindow.navigator.oscpu.toLowerCase().contains("mac os x");
unsafeWindow.document.addEventListener('keydown', function(e) {
  if (e.keyCode === 116) {
    // F5 should never be captured
    e.stopImmediatePropagation();
    return;
  }
  
  // Mac uses the Command key, identified as metaKey
  // Windows and Linux use the Control key, identified as ctrlKey
  var modifier = isMac ? e.metaKey : e.ctrlKey;
  // abort if the proper command/control modifier isn't pressed
  if (!modifier) {
    return;
  }
  
  switch (e.keyCode) {
    case 87: // W - close window
    case 84: // T - open tab
    case 76: // L - focus awesome bar
    case 74: // J - open downloads panel
      e.stopImmediatePropagation();
      return;
  }
  
  // s'more mac love
  if (!isMac) {
      return;
  }
  
  switch (e.keyCode) {
    case 188: // , (comma) - open settings [mac]
    case 82: // R - reload tab
      e.stopImmediatePropagation();
      return;
  }
}, true);
})();
