## Indie Respond

Firefox browser extensions that use [Micropub](https://micropub.net/) to create like, follow, and reply posts on [snarfed.org](https://snarfed.org/) for the currently visible page.

There are three separate extensions, not one, since [Firefox currently only allows one toolbar button per extension](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/user_interface/Browser_action#specifying_the_browser_action), and I want a button for each.

`common.js` and `token.js` are duplicated in each extension because Firefox doesn't allow browser extensions to load files outside of the extension directory, whether by relative `'../` paths or symlinks, and it requires the manifest to be named exactly `manifest.json`, which means a single directory can't have more than one extension.
