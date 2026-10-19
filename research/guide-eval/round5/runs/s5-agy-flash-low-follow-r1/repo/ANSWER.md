# Soft 404 Issue: Cause and Fix

## Cause

The site pages (served under `/n/<slug>` and `/`) are single-page application shells where client-side JavaScript (`/app.js`) dynamically fetches content from `/v1/notes` and `/v1/notes/${slug}`.

On 2026-09-07, `Disallow: /v1/` was added to `site/robots.txt` to prevent web crawlers from hitting unauthenticated POST/PUT endpoints and logging 404/405 errors. Because Googlebot obeys `robots.txt` when fetching subresources while rendering pages, it was blocked from fetching the note data (`/v1/notes/...`).

When `fetch(`/v1/notes/${m[1]}`)` fails in `app.js`, the catch handler renders the fallback UI:
```html
<section class="notfound">
  <h1>NOT FOUND</h1>
  <p>No note lives at this address.</p>
  <p><a href="/">Back to all notes</a></p>
</section>
```
Googlebot rendered this "NOT FOUND" screen on HTTP 200 responses and classified the note pages as **Soft 404**. Note pages published after the robots.txt change (or recrawled after it) could not be indexed, while pages indexed prior to September 7 remained in the index until recrawled.

---

## Fix

Updated `site/robots.txt` using Google's longest-match evaluation rule:
- Added `Allow: /v1/notes` so Googlebot can fetch public note listings (`/v1/notes?limit=50`) and note contents (`/v1/notes/<slug>`).
- Added `Disallow: /v1/notes/*/reactions` to keep the per-user reactions endpoint blocked.
- Kept `Disallow: /v1/` to block all other endpoints (such as `/v1/me`, `/v1/me/drafts`, `/v1/auth/token`, etc.).
- Kept `Disallow: /admin/`.

Under Google's robots.txt parser specification, the longest matching rule wins (and on equal length, `Allow` wins):
- `/v1/notes` and `/v1/notes/<slug>` match `Allow: /v1/notes` (length 9) over `Disallow: /v1/` (length 4) -> **Allowed**.
- `/v1/notes/<slug>/reactions` matches `Disallow: /v1/notes/*/reactions` (length 21) -> **Blocked**.
- `/v1/me`, `/v1/auth/token`, etc. match `Disallow: /v1/` (length 4) -> **Blocked**.

### Updated `site/robots.txt`

```robots.txt
User-agent: *
Allow: /v1/notes
Disallow: /v1/notes/*/reactions
Disallow: /v1/
Disallow: /admin/

Sitemap: https://fieldnotes.example/sitemap.xml
```
