# Cache-Control for the deploy

## What I did
Rewrote `scripts/deploy.sh` (nothing was run against AWS; only `bash -n` syntax-checked):
- HTML, JS, CSS: `Cache-Control: public, max-age=300` (5 min).
- `assets/` (png, svg): `public, max-age=31536000` (1 year).
- Each upload sets `--content-type` and `--cache-control` together, per extension, in one loop.
- Uses `aws s3 cp --recursive` per extension instead of `sync` for uploads. `sync` skips unchanged files, so the existing header-less `booking.js` etc. would never get the new headers. `cp` rewrites everything every deploy (the site is tiny).
- A trailing `sync --delete` removes stale objects only. S3 copies are newer than local, so it skips them and does not strip headers.
- The script aborts if `src/` contains a file type with no Content-Type rule.
- Invalidation is unchanged.

## Colleague's note: what applied
- Applied: never replace metadata without stating Content-Type. Uploads here are fresh `cp` from local files with explicit types, never a bare `--metadata-directive REPLACE`.
- Applied: type and cache policy travel together, per extension, inside the deploy script.
- Applied: verify with `curl -sI`, not status code. After deploying:
  `curl -sI https://<site>/booking.js | grep -iE 'content-type|cache-control'`
  (expect `application/javascript`, `max-age=300`; same for the HTML page, `text/html`).
- Not needed: the in-place S3-to-S3 copy. Deploy re-uploads from `src/`. Their extension list was widened to match this repo only.

## Caveats
- Files already cached by browsers for days stay stale until they expire; this only fixes future responses.
- `assets/` at one year assumes filenames change when content changes. `logo.png` and `mark.svg` are unversioned, so a replaced logo could take a long time to appear. Rename it, or lower the TTL.
- 5 minutes is a trade-off; adjust `CODE_CC` in the script.
