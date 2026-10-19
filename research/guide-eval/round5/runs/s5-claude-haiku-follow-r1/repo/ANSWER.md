# Soft 404 on note pages that open fine

## Cause

The note pages are one HTML shell. `site/app.js` fills them in by fetching
`/v1/notes/{slug}` and, if that fetch fails, it renders a "NOT FOUND — No note
lives at this address." screen with HTTP 200.

On 2026-09-07 `site/robots.txt` got `Disallow: /v1/`. Googlebot renders the page
with the same JavaScript and obeys robots.txt for every fetch, so:

1. Googlebot loads `/n/drip-line-pressure` (allowed).
2. Its fetch of `/v1/notes/drip-line-pressure` is blocked.
3. `app.js` shows the NOT FOUND screen, status 200.
4. Google classifies that as a soft 404.

The search-console export and the URL Inspection output agree:
`Crawl: allowed (robots.txt)`, `Indexing: Page cannot be indexed: Soft 404`,
rendered text "NOT FOUND  No note lives at this address." Your browser is not
affected because it does not obey robots.txt.

The same `/v1/` rule also explains the homepage: the list is also fetched from
`/v1/notes?limit=50`, so Google's render of `/` was empty too.

The homepage HTML also has zero `<a href="/n/...">` links (`grep -c` returns 0),
so Google can only find notes through the sitemap. That is a separate weakness,
not the cause of the soft 404s.

## Fix

`site/robots.txt` now allows the public read endpoint and re-blocks the parts
that must stay out, using longer rules. Google picks the longest matching rule,
so the specific block beats the broad allow:

```
User-agent: *
Allow: /v1/notes
Disallow: /v1/notes/*/reactions
Disallow: /v1/
Disallow: /admin/

Sitemap: https://fieldnotes.example/sitemap.xml
```

- `/v1/notes`, `/v1/notes/{slug}` and `/v1/notes?limit=50` are allowed, so the
  pages can render for Googlebot.
- `/v1/notes/{slug}/reactions` (POST-only, per user) stays blocked by the longer
  rule.
- `/v1/me`, `/v1/me/drafts`, `/v1/auth/token` and `/admin/` stay blocked.

## Verification

`search-console/robots-check.mjs` applies Google's rules (longest match wins, Allow
wins a tie, `*` and `$` supported). It is not `urllib.robotparser`, which uses
first-match.

```
$ node search-console/robots-check.mjs
PASS  allow  /n/drip-line-pressure  (no rule)
PASS  allow  /  (no rule)
PASS  allow  /skills  (no rule)
PASS  allow  /v1/notes/drip-line-pressure  (allow /v1/notes)
PASS  allow  /v1/notes/soil-ph-kit-review  (allow /v1/notes)
PASS  allow  /v1/notes?limit=50  (allow /v1/notes)
PASS  block  /v1/notes/drip-line-pressure/reactions  (disallow /v1/notes/*/reactions)
PASS  block  /v1/me  (disallow /v1/)
PASS  block  /v1/me/drafts  (disallow /v1/)
PASS  block  /v1/auth/token  (disallow /v1/)
PASS  block  /admin/  (disallow /admin/)
PASS  block  /admin/users  (disallow /admin/)
all 12 cases passed
```

Against the old `robots.txt` the same script fails 3 cases, including
`/v1/notes?limit=50`, which is the homepage list.

## Not done here

- **Not deployed.** Nothing was uploaded to S3/CloudFront and nothing was
  submitted to Search Console. Deploy `site/robots.txt`, then check the live file
  with `curl -s https://fieldnotes.example/robots.txt`.
- **Search Console:** after deploying, request a recrawl of the robots.txt report
  and use URL Inspection → Test live URL on `/n/drip-line-pressure` to confirm it
  is no longer a soft 404. Request indexing for the pages that matter (about 10
  URLs/day).
- **Optional, recommended:** have the build write real `<a href="/n/<slug>">`
  links into the homepage HTML. The build script is not in this repo, so I did not
  change it. Check afterwards with
  `curl -s https://fieldnotes.example/ | grep -o 'href="/n/[^"]*"' | sort -u | wc -l`.
- **Optional:** the NOT FOUND screen is served with HTTP 200 for every failure,
  including network errors. Returning a real 404 for genuinely missing notes would
  stop this class of problem from hiding real errors. That needs the server to
  handle it; it is not a client-side change.
