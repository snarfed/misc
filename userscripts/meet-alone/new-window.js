'use strict'

// console.log('@')
browser.tabs.onUpdated.addListener(function(id, change, tab) {
  // console.log('@@')
  // console.log(change.url)
  // if (change.url.startsWith('http://localhost/')) {
  if (change.url.startsWith('https://meet.google.com/')) {
    browser.tabs.query({currentWindow: true}).then(function(tabs) {
      if (tabs.length > 5) {    // heuristic for whether we're in main window
        // console.log('@@@')
        // console.log(change.url)
        // console.log(id)
        browser.windows.create({url: change.url})
        // console.log('@@@@')
        browser.tabs.remove(id)
      }
    })
  }
// }, {urls: ['*://localhost/*']})
}, {urls: ['https://meet.google.com/*']})
