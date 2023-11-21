// ==UserScript==
// @name         Auto Huffduff It
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description	 Automatically clicks the "Huffduff it" button on the https://huffduffer.com/ bookmarklet page
// @author       Ryan https://snarfed.org/
// @match        https://huffduffer.com/add*
// @grant        none

// ==/UserScript==

(function() {
  if (document.location.toString().startsWith('https://huffduffer.com/add?')) {
    console.log('Clicking Huffduff It button')
    document.forms[0].submit()
  }
})();
