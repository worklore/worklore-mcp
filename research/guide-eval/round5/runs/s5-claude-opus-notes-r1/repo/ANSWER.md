# Soft 404 on note pages that load fine

## Cause

`robots.txt` gained `Disallow: /v1/` on 2026-09-07 (to silence crawler 404/405s on
POST-only API paths). But every page is the same empty HTML shell, and `site/app.js`
fills it by fetching `/v1/notes/{slug}` (and `/v1/notes?limit=50` on the home page).

Googlebot obeys robots.txt while rendering too, so the API fetch is blocked. The fetch
fails, the `catch` in `app.js` renders **"NOT FOUND – No note lives at this address"**,
and the page is still served with HTTP 200 and the generic title "Field notes". Google sees
a 200 page that says "not found", which is a Soft 404. The URL Inspection export shows exactly that
rendered text (`search-console/url-inspection-drip-line-pressure.txt`).

Browsers and curl aren't affected because they ignore robots.txt (and curl doesn't run JS).
The timing matches: pages last crawled before Sep 7 (`first-frost-dates` 08-29,
`mulch-depth-trial` 08-31) are still indexed. Every note crawled after that is a Soft 404,
which is why the indexed count fell from 25 to 21 while new notes were being added.

## Fix

1. **`site/robots.txt`**: allow the public read endpoints the pages render from, and keep
   everything else under `/v1/` blocked. Google applies the longest matching rule, so the
   more specific `Disallow` for reactions still beats the `Allow`:

   ```
   User-agent: *
   Allow: /v1/notes
   Disallow: /v1/notes/*/reactions
   Disallow: /v1/
   Disallow: /admin/
   ```

   I checked these rules with a longest-match evaluator (the way Google evaluates them, not Python's
   first-match `robotparser`). Allowed: `/v1/notes`, `/v1/notes?limit=50`, `/v1/notes/<slug>`, `/n/<slug>`.
   Blocked: `/v1/notes/<slug>/reactions`, `/v1/me`, `/v1/me/drafts`, `/v1/auth/token`,
   `/admin/…`. (robots.txt can't filter by HTTP method. Unauthenticated POST/PUT on `/v1/notes`
   return 401 anyway, and crawlers only send GET.)

2. **`site/app.js`** (hardening): only an actual API 404 shows "NOT FOUND", and in that case
   it also sets `<meta name="robots" content="noindex">`. Any other failure (blocked,
   network, 5xx) shows a neutral "Couldn't load this page" message, so a temporary problem no
   longer looks like a missing page.

## After deploying (your side, not done here)

- Check the live file: `curl -s https://fieldnotes.example/robots.txt`.
- In Search Console, request a robots.txt recrawl (Settings → Crawling → robots.txt). Then run
  URL Inspection → Test live URL on `/n/drip-line-pressure`. The rendered page should show
  the note, not the not-found screen. After that, request indexing for the Soft-404 URLs.
- Optional: put plain `<a href="/n/…">` links in the server HTML so discovery doesn't depend
  on JS and the sitemap alone. This would help the "Discovered – currently not indexed" pages.
