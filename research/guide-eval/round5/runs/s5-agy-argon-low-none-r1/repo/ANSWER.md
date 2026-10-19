# Cause and Fix for Soft 404 on Note Pages

## Cause

Note pages (`/n/<slug>`) are rendered client-side as a single-page application (SPA):
1. CloudFront rewrites `/n/<slug>` to `/index.html` and serves the static HTML shell with HTTP `200 OK`.
2. On page load, `site/app.js` fetches the note content from `/v1/notes/<slug>` (or `/v1/notes?limit=50` on the home page).
3. If the `fetch()` call fails or throws an error, `site/app.js` catches the error and renders the fallback message inside `#app`:
   ```
   NOT FOUND
   No note lives at this address.
   Back to all notes
   ```
4. On **2026-09-07**, `Disallow: /v1/` was added to `site/robots.txt` to stop crawlers from hitting POST-only and authenticated `/v1/` endpoints (`api/routes.md`).
5. While regular browsers (`Chrome`, `Safari`) and `curl` do not enforce `robots.txt` for `fetch()` requests, **Googlebot's Web Rendering Service (WRS) obeys `robots.txt` for all subresource and XHR/`fetch()` requests made during JavaScript rendering**.
6. Because `/v1/` is disallowed in `site/robots.txt`, Googlebot blocks the `fetch('/v1/notes/<slug>')` request when rendering `/n/<slug>`. The rejected `fetch` triggers the `catch (e)` block in `site/app.js`, rendering `"NOT FOUND No note lives at this address."` on a page served with HTTP `200`.
7. Google Search Console sees an HTTP `200` page whose rendered body says `"NOT FOUND"` and flags every newly crawled or re-crawled note page after September 7 as a **Soft 404** (while notes last crawled in August, before the `robots.txt` change, remained indexed).

## Fix

Update `site/robots.txt` so crawlers are allowed to access the public read-only note API endpoints (`/v1/notes` and `/v1/notes/{slug}`) required to render the pages, while keeping non-public/POST-only API endpoints (`/v1/me`, `/v1/auth/token`, `/v1/notes/*/reactions`, etc.) disallowed:

```robots
User-agent: *
Allow: /v1/notes$
Allow: /v1/notes?
Allow: /v1/notes/
Disallow: /v1/notes/*/reactions
Disallow: /v1/
Disallow: /admin/

Sitemap: https://fieldnotes.example/sitemap.xml
```
