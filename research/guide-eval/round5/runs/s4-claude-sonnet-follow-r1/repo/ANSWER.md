# Cache-Control for the deploy

## What I changed
`scripts/deploy.sh` only (not run; no AWS calls made).

- Kept `aws s3 sync --delete` as step 1 to mirror `src/` and remove stale objects.
- Added step 2: a per-extension loop of `aws s3 cp src/ s3://… --recursive` that sets
  `--content-type` and `--cache-control` **together**:
  - `*.html`, `*.js`, `*.css`: `public, max-age=300` (5 min)
  - `assets/*.png`, `assets/*.svg`: `public, max-age=86400` (1 day)
- The CloudFront invalidation stays as the last step.

## Why it's built this way
- `sync` skips files whose size/mtime match, so it would never add headers to
  objects already in the bucket. `cp` from the local directory always re-uploads,
  so the first deploy fixes existing objects too.
- It uploads from local files rather than self-copying with
  `--metadata-directive REPLACE`. That flag replaces *all* metadata, and without an
  explicit `--content-type` every object becomes `binary/octet-stream` and the
  site stops rendering. Type and cache policy now can't be applied separately.
- Content types are explicit, and the script's header comment warns against the trap.

## Caveats
- "Long" for `assets/` is 1 day, not a year: the filenames aren't fingerprinted
  (`logo.png`), so a replaced image can be stale for up to a day. Use `immutable`
  and a year only if you add content hashes to filenames.
- Files with other extensions get whatever `sync` guesses and no Cache-Control.
  Add a rule to `RULES` if you add new types.
- Browsers that already cached `booking.js` with no header may still hold it until
  their heuristic freshness expires; the new headers apply after their next fetch.

## Verify after the next deploy (I didn't run it)
A 200 isn't proof. Check the type:
```
curl -sI https://<site>/            | grep -i -E 'content-type|cache-control'  # text/html, max-age=300
curl -sI https://<site>/booking.js  | grep -i -E 'content-type|cache-control'  # application/javascript, max-age=300
```
Then load the site in a browser that has never seen it.
