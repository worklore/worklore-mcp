# Cause and Fix for Search Console Soft 404 Errors

## 1. Why Search Console Reported "Soft 404"

Each note page (e.g. `/n/drip-line-pressure`) is served by an SPA shell (`index.html`) that loads `app.js`. In `app.js`, client-side JavaScript calls:
```javascript
fetch(`/v1/notes/${m[1]}`)
```
to retrieve the note content. If that API fetch fails or is rejected, `app.js` catches the error and renders the fallback error template:
```html
<section class="notfound">
  <h1>NOT FOUND</h1>
  <p>No note lives at this address.</p>
  <p><a href="/">Back to all notes</a></p>
</section>
```
Because the SPA shell itself returns HTTP 200, but Googlebot renders the page and sees a "NOT FOUND - No note lives at this address" message with empty content, Google Search Console classifies it as a **Soft 404**.

On **2026-09-07**, `robots.txt` was configured with:
```robots.txt
Disallow: /v1/
```
Because Googlebot respects `robots.txt` when fetching subresources during JavaScript rendering, it was blocked from fetching `/v1/notes/<slug>`. Consequently:
- Pages crawled before September 7 remained indexed.
- Any notes crawled after September 7 could not fetch their data during rendering, triggered the client-side catch block, rendered the "NOT FOUND" screen, and were marked as "Soft 404".
- Browsers loaded the pages without issue because browsers do not restrict user requests based on `robots.txt`.

---

## 2. The Fix

The fix was applied directly to `site/robots.txt`. We explicitly allow crawling of the public read endpoints required to render the site, block specific non-public subpaths, and maintain the general block on `/v1/`:

```robots.txt
User-agent: *
Allow: /v1/notes$
Allow: /v1/notes?
Allow: /v1/notes/
Disallow: /v1/notes/*/reactions
Disallow: /v1/
Disallow: /admin/

Sitemap: https://fieldnotes.example/sitemap.xml
```

### How Google Evaluates These Rules
Under Google's `robots.txt` specifications:
1. Google uses the **longest matching rule** (by character count). In case of a length tie, `Allow` takes precedence.
2. `/v1/notes` and `/v1/notes?limit=50` (length 9): matched by `Allow: /v1/notes$` and `Allow: /v1/notes?` (winning over `Disallow: /v1/`, length 4).
3. `/v1/notes/<slug>` (e.g., `/v1/notes/drip-line-pressure`): matched by `Allow: /v1/notes/` (length 10, winning over `Disallow: /v1/`).
4. Non-public or per-user endpoints under notes, such as `/v1/notes/<slug>/reactions`: matched by `Disallow: /v1/notes/*/reactions` (length 21), which is longer and takes precedence over `Allow: /v1/notes/`.
5. Other private endpoints (such as `/v1/me`, `/v1/me/drafts`, and `/v1/auth/token`): fall back to `Disallow: /v1/` (blocked).

---

## 3. Colleague's Note: Which Parts Applied

- **Applied:**
  - **Core Cause:** The client-side JavaScript rendering depends on fetching data from an API located on the same domain (`/v1/...`). Googlebot respects `robots.txt` when fetching resources for rendering; the blanket `Disallow: /v1/` rule prevented Googlebot from retrieving note data.
  - **Mechanism of Soft 404:** The failed fetch triggered client-side error handling displaying a "NOT FOUND" message on an HTTP 200 response, which Google evaluates as a Soft 404.
  - **Reproduction Steps 1 & 2:** Checking `robots.txt` disallow rules against `fetch()` targets in `app.js` and verifying what `app.js` displays when the fetch fails.
  - **Fix Strategy (Step 3):** Updating `robots.txt` using Google's longest-match evaluation rules: adding specific `Allow` rules for public read paths (`/v1/notes...`), a longer `Disallow` rule for authenticated sub-routes (`/v1/notes/*/reactions`), and keeping `Disallow: /v1/` for the remaining private API routes.
  - **Rule Verification (Step 4):** Testing route resolution with a longest-match script rather than first-match parser logic.

- **Did Not Apply / Ignored:**
  - **Discovery / Server-side Links (colleague's first theory and Step 6):** The site does not pre-render static HTML links; note URLs are already discovered via `sitemap.xml` (as confirmed by the Search Console exports and `README.md`).
  - **Deploying / Requesting Live Recrawl in Search Console (Steps 5 & 7):** As per instructions, working strictly locally without external deployments or Search Console API requests.
