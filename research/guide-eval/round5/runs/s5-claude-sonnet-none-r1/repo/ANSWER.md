# Soft 404 on note pages

## Cause
Every note page is an empty HTML shell; `site/app.js` fetches the content from
`/v1/notes/<slug>` in the browser. On 2026-09-07 `Disallow: /v1/` was added to
`robots.txt` (to stop crawler 404/405 noise on POST-only routes). Googlebot's
renderer obeys robots.txt for subresource fetches too, so it can no longer load
the note JSON. `app.js` then hits its `catch` branch and renders "NOT FOUND - No
note lives at this address" while the server still returns HTTP 200. Google sees
a 200 page whose rendered text says not found -> Soft 404 (the URL inspection
shows exactly that rendered text, with "Crawl: allowed" for the page itself).

Browsers and curl ignore robots.txt, so the pages look fine to you. That also
explains the timeline: pages crawled in August (before the change) stayed
indexed; every note crawled after Sep 7 is a Soft 404, and indexed count fell
25 -> 21 as old pages were re-crawled. The "Discovered - not indexed" ones
are queued behind the same problem.

## Fix (in this repo)
1. `site/robots.txt`: added `Allow: /v1/notes` (longer match beats `Disallow: /v1/`),
   so the public read endpoints are crawlable. Auth/POST routes stay disallowed.
2. `site/app.js`: the error state now adds `<meta name="robots" content="noindex">`,
   so a failed load is never indexed as a page.

## After you deploy (not done by me)
Deploy robots.txt, then use "Validate fix" / request re-indexing in Search Console
and re-run the live URL test; the rendered text should show the note.
Longer term, pre-render or server-side render note HTML (and return a real 404
status for unknown slugs) so indexing doesn't depend on client-side API calls.
