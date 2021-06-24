/** Caching proxy.
 *
 * Uses the entire path and query parameters as the target URL. Eg if this
 * worker is deployed at caching-proxy.snarfed.worker.dev, a GET to:
 *
 *   https://caching-proxy.snarfed.worker.dev/http://foo.com/bar?baz
 *
 * will request and return:
 *
 *   http://foo.com/bar?baz
 *
 * To run local dev server:
 *
 *    wrangler dev
 *
 * To deploy:
 *
 *    wrangler publish
 *
 * Currently deployed at https://caching-proxy.snarfed.worker.dev/
 * Admin: https://dash.cloudflare.com/dcc4dadb279e9e9e69e9e84ec82d9303/workers/view/caching-proxy
 *
 * Based on:
 * https://developers.cloudflare.com/workers/examples/cache-using-fetch
 * https://github.com/cloudflare/cloudflare-docs/blob/production/products/workers/src/content/examples/cache-using-fetch.md
 */

async function handleRequest(request) {
  const url = new URL(request.url)

  if (url.pathname == '/' || url.pathname == '/favicon.ico') {
    return new Response(null, {status: 404})
  }

  let target = url.pathname.substring(1) + url.search

  // Oddly URL.pathname in Node (but not Firefox) collapses repeated slashes to
  // a single slash, so we need to reconstitute this.
  if (!target.includes('://'))
    target = target.replace(':/', '://')

  let response = await fetch(target, {
    cf: {
      // Always cache this fetch regardless of content type
      // for 30d before revalidating the resource
      cacheTtl: 2592000,
      cacheEverything: true,
    },
  })

  // Reconstruct the Response object to make its headers mutable
  response = new Response(response.body, response)

  // Tell browsers to cache for 30d
  response.headers.set("Cache-Control", "max-age=2592000")

  return response
}

addEventListener("fetch", event => {
  return event.respondWith(handleRequest(event.request))
})
