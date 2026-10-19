# Soft 404 on note pages

## Cause
`site/robots.txt` has had `Disallow: /v1/` since 2026-09-07. Note pages are an HTML shell that `app.js` fills by calling `GET /v1/notes/{slug}`. Googlebot obeys robots.txt when it renders, so it can't fetch that data. `fetch` then fails, and `app.js` shows the "NOT FOUND – No note lives at this address" screen on a page that returns HTTP 200. Google classifies that as a soft 404.

Evidence in `search-console/`:
- The live test for `/n/drip-line-pressure` shows "Page fetch: Successful (HTTP 200)" and rendered text "NOT FOUND".
- The four notes last crawled 2026-10-10 to 10-14 are Soft 404.
- The two notes crawled in August, before the robots change, are still Indexed.
- This matches the drop from 25 to 21 indexed pages while new notes were published.

It works in browsers and curl because they aren't bound by robots.txt for the page's own fetches.

## Fix (robots.txt only, `site/robots.txt`)
```
User-agent: *
Disallow: /v1/
Disallow: /admin/
Allow: /v1/notes
Disallow: /v1/notes/*/reactions
```
- Google uses the longest matching rule, so `Allow: /v1/notes` opens the two public GETs the pages need: `/v1/notes` and `/v1/notes/{slug}`.
- `/v1/notes/*/reactions` (POST-only, per user) stays blocked by a longer rule.
- `/v1/me*`, `/v1/auth/*` and `/admin/` stay blocked by the general rules.
- I checked this with a small longest-match script (not `urllib.robotparser`). Results: the note, list, reactions, me, drafts, auth and admin paths came out as expected.
- Not deployed, since I was asked not to.

## Next steps (you do these)
1. Deploy robots.txt and confirm it with `curl -s https://fieldnotes.example/robots.txt`.
2. In Search Console, request a robots.txt recrawl, then run URL Inspection, Test live URL, on `/n/drip-line-pressure`. The screenshot should show the real note. Then request indexing.
3. Optional, not done: put real `<a href>` links to notes in the served HTML, so discovery doesn't rely on JavaScript or the sitemap. Also consider having `app.js` show "not found" only on a 404, and have the page return a real 404 status.

## Colleague's note: what applied
- Applied: the diagnosis (robots.txt blocking the API the page renders from, giving a 200 "not found" screen), the Allow plus longer Disallow fix, and testing with longest-match rules.
- Not applied: the build-time links in the homepage and story pages (no build step here; left as optional above), and the Search Console recrawl steps (listed above, not performed). Their route names (`/v1/stories`) don't match this API, so I used `/v1/notes`.
