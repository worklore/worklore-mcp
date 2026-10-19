# Cache-Control on deploy

## Problem

`scripts/deploy.sh` uploaded `src/` with `aws s3 sync` and set no
`Cache-Control` header. Browsers then apply their heuristic caching to
`booking.js`, so returning visitors kept the old file for days even though
CloudFront was invalidated on every deploy.

## Change (`scripts/deploy.sh`)

1. `aws s3 sync src/ ... --delete` is unchanged. It still uploads changed
   files and removes deleted ones.
2. New: `aws s3 cp src/ ... --recursive --exclude "assets/*"` with
   `Cache-Control: public, max-age=300, must-revalidate`. This covers
   `*.html`, `booking.js` and `styles.css` at the site root.
3. New: `aws s3 cp src/assets/ ... --recursive` with
   `Cache-Control: public, max-age=31536000`.
4. CloudFront invalidation is unchanged.

Step 2 is needed because `aws s3 sync` skips objects whose size and
timestamp have not changed. Without it, objects already in the bucket would
never receive the header. Re-copying everything once per deploy handles
that. The site is small, so the extra upload is negligible.

## Decisions to review

- **`styles.css` gets the short cache.** The request said "short for HTML
  and JS". The stylesheet sits at the root, not in `assets/`, so it follows
  the short rule. Move it to `assets/` if it should be cached longer.
- **`assets/` is cached for one year without fingerprinting.** Filenames
  such as `logo.png` and `mark.svg` are not versioned. If one of them
  changes, browsers keep the old copy for up to a year. The script comment
  says to rename the file to change it.
- **`must-revalidate` on the short cache.** A stale copy is never reused
  after it expires.

## Verification

- `bash -n scripts/deploy.sh` passes.
- The script was not run, because it deploys to S3 and invalidates
  CloudFront, and the ground rules say not to deploy. The AWS CLI calls are
  untested against the real bucket.

To confirm after the first real deploy:

```sh
aws s3api head-object --bucket ruta-ceramica-site-7f3a --key booking.js \
  --profile studio --query CacheControl
aws s3api head-object --bucket ruta-ceramica-site-7f3a --key assets/logo.png \
  --profile studio --query CacheControl
```

Expected output: `"public, max-age=300, must-revalidate"` and
`"public, max-age=31536000"`.

## Not done

- No deploy, publish or external submission.
- `README.md` still lists the stale-JS problem as open. Update it after the
  change is confirmed in production.
