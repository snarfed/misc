## Indie Respond

Firefox browser extensions that use [Micropub](https://micropub.net/) to create like, follow, and reply posts on [snarfed.org](https://snarfed.org/) for the currently visible page.

There are three separate extensions, not one, since [Firefox currently only allows one toolbar button per extension](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/user_interface/Browser_action#specifying_the_browser_action), and I want a button for each.

`common.js` and `token.js` are duplicated in each extension because Firefox doesn't allow browser extensions to load files outside of the extension directory, whether by relative `'../` paths or symlinks, and it requires the manifest to be named exactly `manifest.json`, which means a single directory can't have more than one extension.

`token.js` should be:

```
const TOKEN = '...'

export {TOKEN}
```

To build and sign a new version of an extension (get the API secret from `bridgy/private_notes`):

```sh
~/src/bridgy/browser-extension/node_modules/.bin/web-ext build
~/src/bridgy/browser-extension/node_modules/.bin/web-ext sign --use-submission-api --channel unlisted --api-key user:14645521:476 --api-secret ...
```

If it times out, the signing service may be down. It's still in the queue, wait a few days, hopefully they'll bring it back up, you'll get an email when they do. Follow the link in the email or open [My Add-ons](https://addons.mozilla.org/en-US/developers/addons), open the version you just uploaded, click on the `.xpi` file link, and Firefox will install the newly signed add-on.
