# Cache-Control Headers for Deploy

## Root Cause
Previously, `scripts/deploy.sh` uploaded all files from `src/` to S3 using a single `aws s3 sync` command without a `--cache-control` flag. When S3 serves objects without a `Cache-Control` header (providing only `Last-Modified` and `ETag`), browsers fall back to HTTP heuristic caching and keep serving cached files like `booking.js` from local disk cache for days—even after CloudFront edge caches are invalidated.

## Changes Made
Updated `scripts/deploy.sh` to split the S3 upload into two `aws s3 sync` steps with explicit `Cache-Control` headers:

1. **Short cache for HTML, JS, and root files (`index.html`, `clases.html`, `booking.js`, `styles.css`):**
   ```bash
   aws s3 sync src/ "s3://$BUCKET/" \
     --exclude "assets/*" \
     --cache-control "public, max-age=300, must-revalidate" \
     --delete --profile "$PROFILE"
   ```
   Sets a 5-minute TTL (`max-age=300`) with `must-revalidate` so browsers re-fetch or revalidate HTML and `booking.js` shortly after a deploy instead of caching them heuristically for days.

2. **Long cache for `assets/` (`assets/logo.png`, `assets/mark.svg`):**
   ```bash
   aws s3 sync src/assets/ "s3://$BUCKET/assets/" \
     --cache-control "public, max-age=31536000, immutable" \
     --delete --profile "$PROFILE"
   ```
   Sets a 1-year TTL (`max-age=31536000, immutable`) for static media assets under `assets/`.

3. **CloudFront invalidation:** Kept the existing `aws cloudfront create-invalidation --paths "/*"` step so CloudFront immediately drops cached edge copies and serves the updated objects and headers from S3.
