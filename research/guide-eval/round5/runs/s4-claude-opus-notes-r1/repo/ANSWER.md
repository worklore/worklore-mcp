# Cache-Control on deploy

## What changed
Only `scripts/deploy.sh` changed. It now uploads with `Cache-Control` set on every object:

| Path | Cache-Control |
|---|---|
| `*.html`, `booking.js`, `styles.css` (everything outside `assets/`) | `public, max-age=300` (5 min) |
| `assets/*` | `public, max-age=2592000` (30 days) |

How it works:
- Three `aws s3 cp --recursive` uploads, run in this order: assets, then JS/CSS, then HTML. HTML goes last so a new page never points at a file that isn't uploaded yet.
- I used `cp` instead of `sync` because `sync` skips files that haven't changed, and the objects already in the bucket would never get the header. `cp` re-uploads everything on every deploy, which is cheap for a site this small.
- After the uploads, `aws s3 sync --delete` still runs, but only to remove deleted files. Everything is already uploaded by then, so it doesn't upload anything.
- The CloudFront invalidation is unchanged. It clears the edge copies that were cached without headers.

## Content-Type is safe
`notes/a-cache-header-tweak-…` describes an outage: an in-bucket copy with `--metadata-directive REPLACE` wiped Content-Type and the site was served as `binary/octet-stream`. This script doesn't do that. It uploads from local files, so the CLI sets Content-Type from each file's extension, the same way the old `sync` did. I left a comment in the script warning not to switch to the REPLACE method.

## Notes / choices you may want to revisit
- **CSS** wasn't mentioned in the request. It isn't in `assets/` and its name stays the same between deploys, so I gave it the short policy like JS.
- **assets/ files have plain names** (`logo.png`, `mark.svg`, no content hash). With a long max-age, a changed logo under the same name can stay stale for up to 30 days. That's why I used 30 days and not the usual 1 year + `immutable`. If you change an asset, rename it. The values are in `SHORT_CACHE` / `LONG_CACHE` at the top of the script.
- Visitors who already have the old `booking.js` cached with no header may keep it until their browser's own heuristic expiry runs out. The fix applies from their next fetch onward.

## Not done
- Nothing was deployed or run against AWS. I only checked the script's syntax (`bash -n`).
- After the next real deploy, check the headers, not just the 200 status:
  ```
  curl -sI https://<site>/ | grep -iE 'content-type|cache-control'
  curl -sI https://<site>/booking.js | grep -iE 'content-type|cache-control'
  curl -sI https://<site>/assets/logo.png | grep -iE 'content-type|cache-control'
  ```
  Expect `text/html`, a JavaScript type, and `image/png`, each with the matching max-age.
