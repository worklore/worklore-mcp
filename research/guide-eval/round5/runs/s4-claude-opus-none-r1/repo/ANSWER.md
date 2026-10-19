# Cache-Control headers for the deploy

## The problem
`scripts/deploy.sh` uploaded everything with `aws s3 sync` and no `Cache-Control`
header. With no header, browsers guess how long to cache (heuristic caching),
so returning visitors kept the old `booking.js` for days. The CloudFront
invalidation only clears the edge cache. It has no effect on browser caches.

## What changed (`scripts/deploy.sh` only)
| Objects | Header |
|---|---|
| everything outside `assets/` (`*.html`, `booking.js`, `styles.css`) | `public, max-age=60, must-revalidate` |
| `assets/*` | `public, max-age=31536000` (1 year) |

- Uploads use `aws s3 cp --recursive` rather than `sync`. `sync` skips files
  that haven't changed, so objects already in the bucket would have kept having
  no header. `cp` re-uploads every file with its header on every deploy. The
  site is only a few files, so this costs very little.
- After that, two `sync --delete` passes (one for `assets/`, one for the rest
  with `--exclude "assets/*"`) remove objects that were deleted from `src/`.
  Each pass sets the matching header in case it uploads anything. Paths
  excluded from the second pass are not touched by its `--delete`.
- The CloudFront invalidation is unchanged.

After the next deploy, a browser uses a cached HTML/JS/CSS file for at most
60 seconds, then checks again (it gets a cheap 304 if nothing changed). If you
want no stale window at all, change `SHORT_CACHE` to `no-cache`.

## Things to know
- **CSS:** you asked for "short for HTML and JS". `styles.css` isn't in
  `assets/`, so it gets the short header too, which is what you want for
  something that changes alongside the HTML.
- **The 1-year cache on `assets/` is only safe if those files never change
  under the same name.** The names aren't fingerprinted (`logo.png`, `mark.svg`).
  If you replace `logo.png` in place, returning visitors could see the old logo
  for up to a year. To change an asset, use a new file name (e.g.
  `logo-v2.png`) and update the HTML. Otherwise, lower `LONG_CACHE`
  (e.g. `max-age=604800` for a week).
- **Visitors who already have the old `booking.js`:** they still hold a copy
  with no header and keep it until their browser decides to check again. Only
  copies fetched after this deploy follow the new rules. From then on the
  problem should not come back.
- **CloudFront:** if the distribution's cache policy honors origin headers
  (the default), edges will also cache for 60 s / 1 year. The `/*` invalidation
  on each deploy still clears them.

## Not done
I didn't run the deploy and didn't contact AWS. I checked the script only with
`bash -n`. After the next deploy, verify with:
`curl -sI https://<site>/booking.js | grep -i cache-control`
