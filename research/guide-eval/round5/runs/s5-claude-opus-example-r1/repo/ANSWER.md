# Soft 404 on note pages: cause and fix

## Cause

`robots.txt` has blocked `/v1/` since 2026-09-07 (`api/routes.md`), and every note page gets its content from `/v1/`.

- Each page is the same HTML shell. `site/app.js` fetches `GET /v1/notes/{slug}` (or `/v1/notes?limit=50` for the home page) and renders the JSON it gets back.
- Googlebot runs that JavaScript when it renders the page, and it obeys robots.txt for the page's sub-requests. So the fetch to `/v1/notes/drip-line-pressure` is never made.
- When the fetch fails, the `catch` in `app.js` shows the generic **"NOT FOUND — No note lives at this address"** screen, and the shell is still served with HTTP 200. A 200 page that says "not found" is exactly what Google calls a Soft 404.
- The URL Inspection export confirms it: the page fetch was "Successful (HTTP 200)" and crawling was "allowed", but the rendered text is "NOT FOUND No note lives at this address." The block is on the API request, not on the page itself, so the "Crawl: allowed" line looks fine.
- The dates match. The pages still indexed were last crawled before Sep 7 (first-frost-dates 08-29, mulch-depth-trial 08-31). Every note crawled since then (10-10 to 10-14) is a Soft 404. That's why the indexed count fell from 25 to 21 while you were publishing. Browsers and curl don't read robots.txt, so the pages look fine to you.

## Fix

**1. `site/robots.txt`: the real fix.** It now allows the public read endpoints and keeps everything else blocked:

```
User-agent: *
Allow: /v1/notes
Disallow: /v1/notes/*/reactions
Disallow: /v1/
Disallow: /admin/
```

Google picks the longest matching rule, and `Allow` wins a tie. So:
- `/v1/notes?limit=50` and `/v1/notes/{slug}` are allowed (`Allow: /v1/notes` is longer than `Disallow: /v1/`).
- `/v1/notes/{slug}/reactions` stays blocked (its rule is longer than the Allow).
- `/v1/me`, `/v1/me/drafts`, `/v1/auth/token` and `/admin/` stay blocked.

`POST`/`PUT /v1/notes` share a path with the public GET list. That's fine: crawlers only send GET, and the writes need a bearer token.

I checked this with `tools/check_robots.py`, which evaluates rules the way Google does (longest match, not Python `robotparser`'s first match). Run it with `python3 -I tools/check_robots.py site/robots.txt`. All 12 cases pass. The old file fails on exactly the two read endpoints the pages need.

**2. `site/app.js`: hardening so this can't happen silently again.** Before, *any* failure showed "NOT FOUND". Now:
- Only a real 404 from the API shows the not-found screen, and that screen also switches `<meta name="robots">` to `noindex`. Real missing notes get dropped from the index cleanly instead of becoming soft 404s.
- Other failures (network error, blocked fetch, 5xx) show "Couldn't load this note".

**After deploying (left to you; I didn't deploy or submit anything):**
1. Check the live file: `curl -s https://fieldnotes.example/robots.txt`.
2. In Search Console, go to Settings → Crawling → robots.txt → Request a recrawl.
3. Use URL Inspection → Test live URL on `/n/drip-line-pressure`. The rendered text should now show the note, not "NOT FOUND".
4. Request indexing for the four Soft 404 URLs.

Expect "Crawled / Indexed" within days to a couple of weeks.

## Which parts of the colleague's note applied

**Applied:**
- **The diagnosis, almost one to one.** A JS-rendered page reads from a same-domain API. That API was disallowed in robots.txt to stop crawler 404s on POST-only routes. Google obeys robots.txt while rendering, so it got the app's 200 "not found" screen and filed it as a Soft 404. The dates line up the same way.
- **Steps 1–5 and 7.** I found the `Disallow` that matches the page's `fetch()` and checked what the page shows when the fetch fails. I rewrote robots.txt as a specific `Allow` plus a longer `Disallow` for the write path, keeping per-user and auth routes blocked. I tested it with a longest-match script, not `urllib.robotparser`. The deploy, curl check and Search Console recrawl are listed above for you to do.

**Adapted:** the paths differ. Here it's `/v1/notes` and `/v1/notes/*/reactions`, not `/v1/stories` and `/stories/*/reproduced`. There is also extra per-user surface that must stay blocked (`/v1/me`, `/v1/auth/token`).

**Not applied:**
- **Step 6 / the "discovery" theory** (plain `<a href>` links in the server HTML). The note itself says that wasn't the cause, and it isn't here either: the Soft 404 URLs *were* crawled. Here every page is one static shell with no build step, so adding it would mean new build tooling. The two "Discovered – currently not indexed" URLs (bean-trellis-v2, greenhouse-vent-timer) are only waiting to be crawled, and the sitemap covers them. Server-rendered links would still help; it's a separate improvement.
- **The "What happened next" outcomes** (Oct 2 recrawl, the counts) describe their site, not this one.

**My addition, not in their note:** the `app.js` change, so that a failed fetch is never shown as "not found" again.
