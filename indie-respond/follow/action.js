import {respond} from './common.js'

browser.browserAction.onClicked.addListener(() => {respond('follow-of', 'follow', {})})
