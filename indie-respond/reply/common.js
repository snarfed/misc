import {TOKEN} from './token.js'

function respond(prop, category, extraParams) {
  browser.tabs.query({active: true, currentWindow: true}).then((tabs) => {
    return tabs[0]
  }).then((tab) => {
    const endpoint = 'https://snarfed.org/wp-json/micropub/1.0/endpoint'
    extraParams[prop] = tab.url
    const opts = {
      method: 'POST',
      body: new URLSearchParams({
        'h': 'entry',
        // sadly Micropub doesn't support HTML content yet
        // TODO: when it does, make this prettier and use embeds again
        // https://github.com/indieweb/wordpress-micropub/issues/283
        'content': tab.title,
        'name': tab.title,
        'mp-syndicate-to[]': 'bridgy-fed',
        'category': category,
        ...extraParams,
      }),
      headers: {'Authorization': `Bearer ${TOKEN}`},
      // don't send browser cookies. oddly WordPress returns 403 if we include
      // both token and browser cookies
      credentials: 'omit',
    }
    console.debug('requesting', endpoint, opts)
    for (name of opts.body) {
      console.log(name, opts.body[name])
    }
    fetch(endpoint, opts)
  })
}

export {respond}
