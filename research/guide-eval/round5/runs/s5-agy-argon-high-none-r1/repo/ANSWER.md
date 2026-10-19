# Why Search Console Reports Soft 404 on Note Pages

## Cause

1. **Client-side rendering depends on `/v1/notes` API requests:**
   Every `/n/<slug>` URL is rewritten by CloudFront to `/index.html` (`HTTP 200`). When the page loads, `site/app.js` fetches the note content from `/v1/notes/<slug>` (and on `/`, fetches the note list from `/v1/notes?limit=50`).

2. **`site/robots.txt` blocks `/v1/` subresource fetches for Googlebot:**
   On `2026-09-07`, `Disallow: /v1/` was added to `site/robots.txt` to stop crawlers from sending `GET` requests to POST-only API paths (`api/routes.md`).
   - Normal browsers (Chrome, Safari) and `curl` do not consult `robots.txt`, so `fetch('/v1/notes/<slug>')` succeeds and every note opens fine.
   - Googlebot's Web Rendering Service (WRS), however, enforces `robots.txt` on subresource requests made during JavaScript rendering (including `fetch()`). While `/n/<slug>` itself is allowed by `robots.txt` and returns `HTTP 200`, Googlebot blocks `fetch('/v1/notes/<slug>')` because it matches `Disallow: /v1/`.

3. **Blocked `fetch()` renders the "NOT FOUND" fallback on an HTTP 200 page (Soft 404):**
   When Googlebot blocks the `fetch()` call, the promise rejects and `site/app.js` falls into its `catch (e)` block, leaving `<title>` as `"Field notes"` and rendering:
   ```html
   <section class="notfound"><h1>NOT FOUND</h1><p>No note lives at this address.</p><p><a href="/">Back to all notes</a></p></section>
   ```
   Google sees an `HTTP 200` response whose rendered DOM says `"NOT FOUND No note lives at this address. Back to all notes"` (as seen in `search-console/url-inspection-drip-line-pressure.txt`) and classifies the page as a **Soft 404**. Consequently, notes crawled after `2026-09-07` failed with Soft 404 instead of being indexed (dropping the indexed page count from 25 on Sep 1 to 21 on Oct 16 as 4 notes were crawled in October).

## Fix

Update `site/robots.txt` to allow crawling the public note read endpoints (`GET /v1/notes` and `GET /v1/notes/{slug}`) while keeping the POST-only reactions endpoint (`/v1/notes/{slug}/reactions`) and the rest of `/v1/` (`/v1/me`, `/v1/me/drafts`, `/v1/auth/token`) disallowed:

```robots.txt
User-agent: *
Allow: /v1/notes
Disallow: /v1/notes/*/reactions
Disallow: /v1/
Disallow: /admin/

Sitemap: https://fieldnotes.example/sitemap.xml
```
