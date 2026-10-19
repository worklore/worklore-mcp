# Soft 404 on note pages that load fine in a browser

## Cause

`site/robots.txt` has had `Disallow: /v1/` since 2026-09-07 (added to stop crawlers
logging 404/405s on POST-only API paths, per `api/routes.md`). But every note page
is an empty HTML shell that `site/app.js` fills by fetching
`/v1/notes/{slug}` (home page: `/v1/notes?limit=50`), and **Googlebot obeys
robots.txt when it renders, too**.

So Google fetches `/n/drip-line-pressure` (HTTP 200), runs `app.js`, gets blocked
from fetching `/v1/notes/drip-line-pressure`, the `fetch` fails, and the `catch` block
draws the "NOT FOUND — No note lives at this address" screen. A not-found
screen served with HTTP 200 is exactly what Google calls a **soft 404**. The URL
Inspection export shows it: "Crawl: allowed", "Page fetch: Successful (HTTP 200)",
rendered text "NOT FOUND No note lives at this address."

The dates line up. Notes crawled before Sep 7 (`first-frost-dates` 08-29,
`mulch-depth-trial` 08-31) are still indexed. Everything crawled after that is a
Soft 404, and as older pages were re-crawled they dropped out too (25 → 21 indexed).
Browsers and curl don't read robots.txt, which is why the pages look fine for you.

## Fix (robots.txt only, `site/robots.txt`)

```
User-agent: *
Allow: /v1/notes$
Allow: /v1/notes?
Allow: /v1/notes/
Disallow: /v1/notes/*/reactions
Disallow: /v1/
Disallow: /admin/

Sitemap: https://fieldnotes.example/sitemap.xml
```

Google uses the **longest matching rule**, and `Allow` wins a tie. So:

| Path | Result | Rule that wins |
|---|---|---|
| `/v1/notes?limit=50` (home list) | allowed | `Allow: /v1/notes?` |
| `/v1/notes/{slug}` (a note) | allowed | `Allow: /v1/notes/` |
| `/v1/notes/{slug}/reactions` (POST, per user) | blocked | `Disallow: /v1/notes/*/reactions` (longer) |
| `/v1/me`, `/v1/me/drafts`, `/v1/auth/token` | blocked | `Disallow: /v1/` |
| `/admin/...` | blocked | `Disallow: /admin/` |

Per-user and auth endpoints stay blocked. `POST /v1/notes` and `PUT /v1/notes/{slug}` use the
same paths as the public GETs, so crawlers will request them with GET and get the
public JSON back. That causes no errors.

I tested this with a small longest-match evaluator (not Python's `urllib.robotparser`,
which applies the first matching rule): all 13 cases pass. Against the old file, the three
public read paths come out blocked, which confirms the cause.

## After deploying (not done here; no external actions taken)

1. `curl -s https://fieldnotes.example/robots.txt` and check it is the new file
   (watch for CloudFront caching; invalidate `/robots.txt` if needed).
2. Search Console → Settings → Crawling → robots.txt → ⋮ → Request a recrawl.
3. URL Inspection → Test live URL on `/n/drip-line-pressure`. It should say the
   page can be indexed, and the screenshot should show the note, not NOT FOUND. Then
   Request indexing for the Soft 404 and "Discovered" URLs (about 10 per day).
4. Expect the pages to move to Crawled and then Indexed over days to about two weeks.

Optional hardening (not required for this fix): give `index.html` server-side
`<a href="/n/...">` links so discovery doesn't depend only on the sitemap and JS.
Also make `app.js` tell a real 404 from a failed fetch (and add
`<meta name="robots" content="noindex">` only for a real 404), so a temporary API
failure is never rendered as "not found".
