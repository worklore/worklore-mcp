# Cause and Fix for Search Console Soft 404

## Cause
Googlebot renders client-side JavaScript pages when crawling. On this site, every page is served as an HTML shell (`site/index.html`) where `site/app.js` fetches content dynamically from the API:
- Note pages fetch `/v1/notes/{slug}`.
- The homepage fetches `/v1/notes?limit=50`.

In September 2026, `Disallow: /v1/` was added to `site/robots.txt` to prevent crawlers from hitting unauthenticated POST/PUT endpoints. Because Googlebot respects `robots.txt` when fetching subresources during rendering, it was blocked from fetching `/v1/notes/{slug}`. When the API request failed in `app.js`, the catch block rendered the fallback not-found screen:
`"NOT FOUND No note lives at this address. Back to all notes"` with an HTTP 200 status code. Google Search Console detected the 200 response with a "not found" body and flagged the pages as **Soft 404**.

Pages crawled prior to the `robots.txt` change in late August stayed indexed, while newly crawled pages were flagged as Soft 404.

## Fix
Update `site/robots.txt` to allow the public read endpoints required for client-side rendering while keeping POST-only, reaction, and private endpoints blocked using Google's longest-match rule:

```txt
User-agent: *
Allow: /v1/notes
Disallow: /v1/notes/*/reactions
Disallow: /v1/
Disallow: /admin/

Sitemap: https://fieldnotes.example/sitemap.xml
```

- `Allow: /v1/notes` matches `/v1/notes` (homepage list) and `/v1/notes/{slug}` (note pages).
- `Disallow: /v1/notes/*/reactions` has a longer match prefix than `Allow: /v1/notes`, keeping reaction mutations blocked.
- `Disallow: /v1/` blocks all other API routes (`/v1/me`, `/v1/auth/token`, etc.).
