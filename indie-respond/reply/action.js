import {respond} from './common.js'

function start(event) {
  startAsync()
}

document.addEventListener('DOMContentLoaded', start)

async function startAsync() {
  text = document.getElementById('text')
  text.focus()

  // load saved text
  const val = await browser.storage.local.get(['text'])
  if (val && !text.value) {
    const stored = await browser.storage.local.get(['text'])
    if (stored) {
      text.value = stored['text']
    }
  }

  async function saveText(unused) {
    await browser.storage.local.set({'text': text.value})
  }

  // save text on typing and on window close
  text.addEventListener('keydown', (event) => {
    if (event.key == 'Escape')
      window.close()
    browser.alarms.create('save-text', {delayInMinutes: .02})
  })
  addEventListener('visibilitychange', saveText)

  async function debounce(alarm) {
    if (alarm.name == 'save-text')
      await saveText(alarm)
  }
  browser.alarms.onAlarm.addListener(debounce)

  document.getElementById('submit').addEventListener('click', (event) => {
    respond('in-reply-to', 'reply', {
      content: [{html: marked.parse(text.value)}]
    })
    // TODO: window.close() here. the problem is that stops this JS from
    // running, including the HTTP request.
  })
}
