# Soft 404 on note pages: cause and fix

## Cause

Note pages are a client-side app. `/n/<slug>` returns the same HTML shell
(`site/index.html`, title "Field notes"), and `site/app.js` fills in the note by
calling the API at `/v1/notes/<slug>`.

On 2026-09-07 `/v1/` was added to `site/robots.txt` as `Disallow: /v1/`. That rule
also blocks Googlebot from fetching the API. When Google renders a note page, the
`fetch()` to `/v1/notes/<slug>` is refused, so `app.js` falls into its `catch`
block and renders:

    <h1>NOT FOUND</h1><p>No note lives at this address.</p>

The HTTP status is still 200, and the page has no real content. That is a soft
404. Browsers are not affected because robots.txt applies only to crawlers.

The Search Console data fits this:

- `url-inspection-drip-line-pressure.txt` shows "Crawl: allowed (robots.txt)"
  for the page itself, and "Rendered page text: NOT FOUND ... No note lives at
  this address." That is the `catch` text, not a real missing note.
- `pages-2026-10-16.csv`: the two notes indexed before the robots change were last
  crawled on 08-29 and 08-31. Every note crawled after 09-07 is "Soft 404".
- Indexed pages went from 25 (Sep 1) to 21 (Oct 16) while nine notes were added.

Note that the `catch` block also turns any API failure (network error, 5xx, bad
JSON) into the same "NOT FOUND" message, so the problem could hide other errors.

## Fix

1. `site/robots.txt`: removed the blanket `Disallow: /v1/`. Crawlers can now fetch
   the GET content endpoints. The paths that were the reason for the change are
   still blocked: `/v1/auth/`, `/v1/me`, and `/v1/notes/*/reactions`. The
   September 404/405 noise came from crawlers requesting POST-only paths, which
   were not allowed by `Disallow: /v1/`.
2. `site/app.js`: a 404 from the API still shows "NOT FOUND". Any other failure
   now shows "Couldn't load this page" and logs the error to the console, so an
   API problem is no longer reported as a missing note.

## Not done here (needs the deployed system)

- **Real 404 status for missing slugs.** CloudFront rewrites `/n/*` to
  `/index.html`, which returns 200 for every slug. Once the API is reachable, a
  nonexistent note still gets a 200 shell with "NOT FOUND" text, which Google
  will call a soft 404. The clean fix is to return HTTP 404 for unknown slugs
  (CloudFront custom error response or a Lambda@Edge/CloudFront Function that
  checks the API), or to prerender note HTML so the content does not depend on
  client-side JS. The API code is not in this repo, so I could not change it.
- **Re-check after deploy.** Google re-renders on its own schedule. Request
  re-indexing in Search Console only after the new `robots.txt` and `app.js` are
  live and a URL Inspection test shows the note text. I have not deployed or
  submitted anything.
- **The home page** calls `/v1/notes?limit=50` and was also blocked by the same
  rule. The CSV still shows it as "Indexed" (last crawled 10-15), so that status
  may be stale. Check it in the next crawl.
- **Two notes not yet crawled** (`bean-trellis-v2`, `greenhouse-vent-timer`) are
  "Discovered - currently not indexed". They may be affected in the same way, and
  should be checked after the deploy.

I checked the changes by reading them and running `node --check site/app.js`. I
did not load the site live, because the ground rules limit work to this
directory.
