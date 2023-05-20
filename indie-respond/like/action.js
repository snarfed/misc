import {respond} from './common.js'

browser.browserAction.onClicked.addListener(() => {respond('like-of', 'like', {})})
