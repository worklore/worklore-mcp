# Soft 404 on note pages that load fine

## Cause
Every page is one HTML shell; `site/app.js` fetches the note from `/v1/notes/<slug>`
and renders it. On 2026-09-07 `Disallow: /v1/` was added to `site/robots.txt`
(to stop crawler 404/405 noise on POST-only paths). Googlebot obeys robots.txt
for the fetches it makes while rendering, so it can't load the note JSON.
The `fetch` fails, `app.js` falls into its catch block and renders
"NOT FOUND – No note lives at this address" with HTTP 200 (CloudFront rewrites
`/n/*` to `/index.html`). Google sees a "not found" page served as 200: a soft 404.
Evidence: URL inspection shows the rendered title "Field notes" and the NOT FOUND text with
fetch Successful (HTTP 200); notes crawled before 09-07 (first-frost-dates, mulch-depth-trial)
stay indexed, those crawled after (drip-line-pressure, compost-thermometer-week-3, soil-ph-kit-review,
rain-barrel-overflow) are soft 404. Browsers/curl aren't bound by robots.txt, so they look fine.

## Fix
1. `site/robots.txt`: keep `Disallow: /v1/`, add `Allow: /v1/notes` (public read routes the pages
   need), and re-block the POST-only path with a longer rule `Disallow: /v1/notes/*/reactions`.
   Google uses the longest matching rule, so `/v1/me`, `/v1/auth`, drafts etc. stay blocked.
2. `site/app.js` (hardening): the error screen now adds `<meta name="robots" content="noindex">`,
   so a future failed render is not indexed as a page. Only a real 404 from the API is treated as "not found".

## Next steps (not done, I deployed nothing)
Deploy robots.txt, then use "Validate fix" / request re-crawl in Search Console.
The two "Discovered - currently not indexed" notes are a separate, slower matter (young
pages, few links; the homepage list is JS-rendered, so consider server-rendered links).
