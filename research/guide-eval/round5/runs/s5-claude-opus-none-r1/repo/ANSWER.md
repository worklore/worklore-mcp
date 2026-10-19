# Soft 404 on note pages: cause and fix

## Cause

The `Disallow: /v1/` line added to `robots.txt` on 2026-09-07 blocks Googlebot
from the API that the note pages need to render.

- Every `/n/<slug>` URL returns the same HTML shell with HTTP 200. The note
  itself only shows up after `site/app.js` runs and fetches
  `GET /v1/notes/<slug>`.
- Googlebot follows robots.txt for the resources it fetches while rendering,
  not just for page URLs. Because `/v1/` is disallowed, that fetch is blocked
  in Google's renderer.
- `app.js` puts every failure in one `catch` block, and that block draws
  **"NOT FOUND — No note lives at this address."** So Google gets a 200
  response whose page says "not found", which is exactly what a Soft 404 is.
  The URL Inspection live test shows this: HTTP 200, title is the bare shell
  `"Field notes"`, and the text is the not-found message.
- Browsers and curl ignore robots.txt, so the pages look fine to you.
- This matches the timeline. Pages indexed before September keep their old
  index entry until Google recrawls them. Every page crawled since the change
  (the 2026-10-10 to 10-14 crawls in the CSV) turns into a Soft 404, and the
  new notes never get indexed. That's why the count dropped from 25 to 21
  while you added nine notes.

## Fix

1. **`site/robots.txt`**: let crawlers read the public API and keep the
   write-only and auth paths blocked. That last part is what the original
   rule was for (the GET-on-POST-only 404/405 noise).
   ```
   Allow: /v1/notes$
   Allow: /v1/notes?
   Allow: /v1/notes/
   Disallow: /v1/notes/*/reactions
   Disallow: /v1/
   ```
   Google applies the most specific (longest) matching rule. So
   `/v1/notes`, `/v1/notes?limit=50` and `/v1/notes/<slug>` are allowed, while
   `/v1/notes/<slug>/reactions`, `/v1/me*` and `/v1/auth/token` stay blocked.

2. **`site/app.js`**: stop showing "NOT FOUND" for errors that aren't 404s.
   - Only an actual `404` from `/v1/notes/<slug>` shows the not-found page.
     In that case it also sets `<meta name="robots" content="noindex">`, so a
     missing note is dropped cleanly instead of being reported as a Soft 404.
   - Any other failure (blocked request, network error, 5xx) shows "Couldn't
     load this page". The next time something goes wrong, real notes won't be
     labelled as missing.

## After deploying (left to you; nothing was deployed)

- Google caches robots.txt for up to about 24 hours. Then run a URL
  Inspection **live test** on `/n/drip-line-pressure`. The rendered title
  should be `Drip line pressure · Field notes` and the page should show the
  note text.
- Use "Validate fix" on the Soft 404 issue in the Pages report and resubmit
  the sitemap.
- Longer term, consider pre-rendering or server-rendering the note HTML (and
  `<title>`) into `/n/<slug>`. Then indexing won't depend on Google running
  JS and fetching a second resource.
