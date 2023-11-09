import {respond} from './common.js'

document.addEventListener('DOMContentLoaded', (event) => {
  document.getElementById('text').focus()
  document.getElementById('submit').addEventListener('click', (event) => {
    respond('in-reply-to', 'reply', {
      content: [{html: marked.parse(document.getElementById('text').value)}]
    })
  })
})
