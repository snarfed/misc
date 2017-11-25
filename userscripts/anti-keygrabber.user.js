// ==UserScript==
// @name anti key-grabber
// @description Prevent web apps from capturing and muting vital keyboard shortcuts
// @grant none
// @version 1.1
// ==/UserScript==

// Based on:
// https://gist.github.com/rodneyrehm/5213304
// https://blog.rodneyrehm.de/archives/23-Reclaim-Your-Keyboard-Shortcuts-in-Firefox.html
//
// My modifications:
// * handle control *and* meta modifiers
// * added lots more key codes
// * special case arrow keys

(function(){
//var isMac = window.navigator.oscpu.toLowerCase().contains("mac os x");
window.document.addEventListener('keydown', function(e) {
//	console.log('@  ' + e.key + ' ' + e + ' ' + e.metaKey + e.ctrlKey + e.getModifierState('Control') + e.getModifierState('Meta'))

  // e.metaKey and e.ctrlKey are always false for arrow keys, not sure why, so catch them early.
  switch (e.key) {
    case "ArrowDown":
    case "ArrowLeft":
    case "ArrowRight":
    case "ArrowUp":
      e.stopImmediatePropagation();
      e.stopPropagation();
      return;
  }

  // Mac uses the Command key, identified as metaKey
  // Windows and Linux use the Control key, identified as ctrlKey
  // var modifier = isMac ? e.metaKey : e.ctrlKey;
  // abort if the proper command/control modifier isn't pressed
  if (!(e.metaKey || e.ctrlKey)) {
    return;
  }

//	console.log('@ examining')
  switch (e.key) {
    case "a":
    case "c":
    case "e":
    case "j":
    case "k":
    case "l":
    case "t":
    case "v":
    case "w":
    case "y":
    case "z":
    case "0":
    case "1":
    case "2":
    case "3":
    case "4":
    case "5":
    case "6":
    case "7":
    case "8":
    case "9":
    case "Backspace":
//			console.log('@ stopping')
      e.stopImmediatePropagation();
      e.stopPropagation();
      return;
  }
}, true);
})();
