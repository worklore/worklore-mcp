# Soft 404 on note pages that load fine in a browser

## Cause

`site/robots.txt` contains `Disallow: /v1/` (added 2026-09-07, per `api/routes.md`).
The note page and the home list render from the API under `/v1/`:

- `site/app.js:7` fetches `/v1/notes/${slug}` for a note page.
- `site/app.js:13` fetches `/v1/notes?limit=50` for the home list.

Googlebot obeys robots.txt when it renders a page, so it cannot fetch that data.
The `catch` in `app.js` then writes the "NOT FOUND / No note lives at this address"
screen into the page. CloudFront serves the shell with HTTP 200, so Google sees a
successful page whose content says the page does not exist. That is a soft 404.

It fits the evidence:

- `search-console/url-inspection-drip-line-pressure.txt` shows HTTP 200, the rendered
  text "NOT FOUND No note lives at this address", and "Soft 404".
- `search-console/pages-2026-10-16.csv` shows the soft-404 pages were crawled after
  the rule went in. The indexed pages (`first-frost-dates` on Aug 29, `mulch-depth-trial`
  on Aug 31) were crawled before it.
- The same rule blocks the home list, so the home page is also affected for Google.

Caveat: the inspection export does not include Search Console's "blocked resources"
section. Confirm `/v1/notes/...` is listed there in the live test before you rely on it.

## Fix

`site/robots.txt` now allows the public read endpoint and keeps everything else blocked:

```
User-agent: *
Allow: /v1/notes
Disallow: /v1/
Disallow: /v1/notes/*/reactions
Disallow: /admin/
```

- `Allow: /v1/notes` covers `/v1/notes`, `/v1/notes?limit=50` and `/v1/notes/{slug}`.
- `Disallow: /v1/` still blocks `/v1/me`, `/v1/me/drafts`, `/v1/auth/token` and the rest of the API.
- `Disallow: /v1/notes/*/reactions` is longer than the Allow, so it still wins. It is the
  POST-only path that crawlers were hitting.

I checked the rules with `scripts/check-robots.mjs`, which applies Google's rule: the
longest match wins, and Allow wins a tie. The old file fails 3 of 10 cases and the new
file passes all 10:

```
node scripts/check-robots.mjs site/robots.txt
```

The script only reads the `User-agent: *` group. It is not a full robots.txt parser.

## Not done here

- **Deploy.** Nothing has been deployed or submitted. The live file is still the old one
  until you upload `site/robots.txt`. Check it with `curl -s https://fieldnotes.example/robots.txt`.
- **Search Console.** After deploy: Settings → Crawling → robots.txt → Request a recrawl,
  then URL Inspection → Test live URL on `drip-line-pressure` and request indexing.
  Expect the page to render the real note.
- **Discovery (separate from the soft 404).** `bean-trellis-v2` and `greenhouse-vent-timer`
  are "Discovered – currently not indexed" with no crawl date, so Google has not fetched them
  at all. The homepage HTML has no `<a href>` links to notes, and the sitemap in the repo is
  truncated (`<!-- 53 more -->`). Real server-rendered links would help. That is a build change,
  so I left it out.
- **Error screen.** `app.js` shows "NOT FOUND" for every failed fetch, including network errors
  and 5xx responses. Only a real 404 should show that screen. Changing it would not turn a 200
  into a 404 on this static host, but it would stop future outages from looking like missing pages.

## How the colleague's note applied

Applied directly:
- The cause: a robots.txt `Disallow` on the API blocks the data a JavaScript page renders from,
  and the failure screen is served with HTTP 200.
- The fix: `Allow` the public read endpoints, keep the general `Disallow`, and re-block the
  POST-only path with a longer rule. Longest match wins.
- The test method: write a checker that uses longest-match. Do not use `urllib.robotparser`.
- The optional step on server-rendered links (step 6), which matches the discovery gap above.

Did not apply, or not verified here:
- The timeline and results (recrawl on Oct 2, the status changes two days later). Those are the
  colleague's data and say nothing about this site. I have no recrawl results for this site.
- Steps 5 and 7 (live-file check, Search Console recrawl and indexing requests). These need a
  deploy and access to Search Console, which I did not do. See "Not done here".
- `/admin/` is also in this site's robots.txt. I left it blocked and did not change it.
