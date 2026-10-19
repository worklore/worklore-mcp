# Why Search Console reports Soft 404

The note URL returns the shared HTML shell with HTTP 200. JavaScript then loads the note from `/v1/notes/<slug>`. The old `robots.txt` blocked **all** `/v1/` URLs, including that public JSON endpoint. A normal browser can fetch it, but Googlebot rendering must obey the robots rule. Its note request therefore fails; `app.js` caught every failed request and rendered “NOT FOUND” while leaving the page at HTTP 200. The URL Inspection export confirms this exact rendered text and the generic “Field notes” title for `/n/drip-line-pressure`. Search Console classified that 200 response with missing-page content as a Soft 404.

# Fix

- `site/robots.txt` now allows the public `/v1/notes` list and `/v1/notes/<slug>` requests needed to render pages. It still blocks the private account/auth paths, reaction endpoint, and `/admin/`. Robots rules apply to URLs, not HTTP methods, so they cannot block POST or PUT on a public note URL while allowing GET there.
- `site/app.js` now shows “NOT FOUND” only when the note API actually returns 404. Other API or network failures show a temporary-unavailable message instead of falsely saying the note does not exist.

This addresses the affected live note pages after these files are served and Google recrawls them. Search Console's “Discovered - currently not indexed” rows have no crawl or Soft 404 verdict yet. A truly missing slug still gets the site's HTTP 200 shell because of the current CloudFront rewrite; returning an HTTP 404 for that case would require an edge/server routing change outside this static front end.
