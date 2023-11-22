import {TOKEN} from './token.js'

function respond(prop, category, extraParams) {
  browser.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name == 'clear-badge')
      browser.browserAction.setBadgeText({text: ''})
  })

  browser.tabs.query({active: true, currentWindow: true}).then((tabs) => {
    return tabs[0]
  }).then((tab) => {
    const endpoint = 'https://snarfed.org/wp-json/micropub/1.0/endpoint'
    extraParams[prop] = tab.url
    const opts = {
      method: 'POST',
      body: JSON.stringify({
        type: ['h-entry'],
        properties: {
          name: [tab.title],
          'mp-syndicate-to[]': 'bridgy-fed',
          category: [category],
          ...extraParams,
        }
      }),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${TOKEN}`,
      },
      // don't send browser cookies. oddly WordPress returns 403 if we include
      // both token and browser cookies
      credentials: 'omit',
    }

    console.debug('requesting', endpoint, opts)
    browser.alarms.create('clear-badge', {delayInMinutes: .3})
    browser.browserAction.setBadgeBackgroundColor({color: 'yellow'})
    browser.browserAction.setBadgeText({text: '⏱️'})
    return fetch(endpoint, opts)
  }).then((resp) => {
    browser.alarms.create('clear-badge', {delayInMinutes: .2})
    if (resp.ok) {
      browser.browserAction.setBadgeBackgroundColor({color: 'lime'})
      browser.browserAction.setBadgeText({text: '✅'})
    } else {
      browser.browserAction.setBadgeBackgroundColor({color: 'orangered'})
      browser.browserAction.setBadgeText({text: '🆘'})
    }
  }).catch((err) => {
    console.error(err)
    browser.alarms.create('clear-badge', {delayInMinutes: .2})
    browser.browserAction.setBadgeBackgroundColor({color: 'orangered'})
    browser.browserAction.setBadgeText({text: '🆘'})
  })
}

export {respond}
