# Soft 404 on Note Pages: Cause, Fix, and Applicable Parts of Colleague's Note

## Cause

1. **Client-side rendering from a same-domain API**: Every note URL (`/n/<slug>`) and the homepage (`/`) serve the same static HTML shell (`site/index.html`) with HTTP `200`. Client-side JavaScript (`site/app.js`) then fetches the content from the same-domain API:
   - `GET /v1/notes/<slug>` on note pages (`/n/<slug>`)
   - `GET /v1/notes?limit=50` on the homepage (`/`)
2. **`robots.txt` blocked the API fetches during Googlebot rendering**: On `2026-09-07`, `Disallow: /v1/` was added to `site/robots.txt` to stop crawlers from sending `GET` requests to `POST`-only endpoints and logging 404/405 errors (`api/routes.md`). While regular browsers ignore `robots.txt` (so notes open fine in Chrome, Safari, and `curl`), Googlebot obeys `robots.txt` for subresource `fetch()` calls when rendering JavaScript.
3. **Failed fetch renders a "NOT FOUND" message on an HTTP 200 page**: When Googlebot blocks `fetch("/v1/notes/<slug>")`, the promise rejects and triggers the `catch` block in `site/app.js` (lines 18–20), which replaces `#app` with:
   ```html
   <section class="notfound"><h1>NOT FOUND</h1><p>No note lives at this address.</p><p><a href="/">Back to all notes</a></p></section>
   ```
   Because the server returned `HTTP 200` while the rendered page displays `"NOT FOUND No note lives at this address."` (confirmed in `search-console/url-inspection-drip-line-pressure.txt`), Google classifies the page as a **Soft 404**. Notes crawled before `2026-09-07` (`first-frost-dates`, `mulch-depth-trial`) stayed indexed, whereas new or recrawled notes after that date (`drip-line-pressure`, `compost-thermometer-week-3`, `soil-ph-kit-review`, `rain-barrel-overflow`) were marked as `Soft 404`.

---

## Fix

Updated `site/robots.txt` using Google's longest-match (most specific path rule) precedence so Googlebot can fetch the public read endpoints while keeping `POST`-only, per-user, auth, and admin endpoints disallowed:

```robots
User-agent: *
Allow: /v1/notes
Disallow: /v1/notes/*/reactions
Disallow: /v1/
Disallow: /admin/

Sitemap: https://fieldnotes.example/sitemap.xml
```

How Google evaluates each route under these rules:
- `GET /v1/notes` (e.g., `/v1/notes?limit=50`) and `GET /v1/notes/{slug}` (e.g., `/v1/notes/drip-line-pressure`) match `Allow: /v1/notes` (length 9), which beats `Disallow: /v1/` (length 4) → **Allowed**.
- `POST /v1/notes/{slug}/reactions` matches `Disallow: /v1/notes/*/reactions` (length 21), which beats `Allow: /v1/notes` (length 9) → **Disallowed**.
- `/v1/me`, `/v1/me/drafts`, and `/v1/auth/token` only match `Disallow: /v1/` (length 4) → **Disallowed**.
- `/admin/` matches `Disallow: /admin/` → **Disallowed**.

---

## Which Parts of the Colleague's Note Applied

### Applied
- **Core diagnosis**: The exact mechanism—`Disallow: /v1/` in `robots.txt` blocking same-origin `fetch()` calls during Googlebot rendering, causing the JS error handler to render a `"NOT FOUND"` screen on an `HTTP 200` shell, and producing Soft 404s starting on `2026-09-07`—applied directly.
- **Step 1 (Compare `robots.txt` `Disallow` rules against JS `fetch` calls)**: Applied locally by inspecting `site/robots.txt` (`Disallow: /v1/`) against `site/app.js` (`fetch('/v1/notes/...')`).
- **Step 2 (Verify what the app renders when `fetch` fails)**: Applied by checking the `catch` block in `site/app.js` and matching its `"NOT FOUND — No note lives at this address."` output to `search-console/url-inspection-drip-line-pressure.txt`.
- **Step 3 (Fix `robots.txt` only, using longest-match rules)**: Applied, adapting the colleague's route names (`/v1/stories` and `/v1/stories/*/reproduced`) to this site's API routes in `api/routes.md` (`Allow: /v1/notes` and `Disallow: /v1/notes/*/reactions`, while keeping `Disallow: /v1/` for `/v1/me`, `/v1/me/drafts`, and `/v1/auth/token`).
- **Step 4 (Verify rules using Google's longest-match semantics rather than first-match `urllib.robotparser`)**: Applied to verify all site and API routes in `api/routes.md`.

### Did Not Apply (Ignored)
- **Prerequisites / asking for URLs or querying the Search Console API**: All site files, API route documentation, and Search Console exports were already present locally in the workspace.
- **The colleague's specific paths (`/v1/stories`, `/v1/stories/*/reproduced`, `/skills`)**: Replaced with this project's paths (`/n/<slug>`, `/v1/notes`, `/v1/notes/*/reactions`).
- **"First theory: discovery" & Step 6 (Baking static `<a href>` links into server-side HTML via a build step)**: Not applicable here. As noted in the colleague's writeup, discovery was not the cause of the Soft 404s (`sitemap.xml` already lists the note URLs, and unblocking `/v1/notes` also allows Googlebot to render the homepage link list). Moreover, this repository has no build script or local database of all 58 notes—only the static SPA shell `site/index.html`.
- **Step 5 & Step 7 / Verify (Deploying, curling the live site, and requesting recrawls/live tests in Google Search Console)**: Ignored because there is no live deployment and the ground rules require working strictly inside the current directory without contacting external services.
