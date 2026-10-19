# Cache-Control Headers Added to Deploy (`scripts/deploy.sh`)

## Summary of Changes

Updated `scripts/deploy.sh` to attach explicit `Cache-Control` and `Content-Type` metadata headers during S3 deployment before triggering the CloudFront invalidation:

1. **Short Cache TTL (`public, max-age=300` — 5 minutes) for HTML, JS (`booking.js`), and CSS:**
   - Configured short-lived `Cache-Control: public, max-age=300` headers for `.html`, `.js`, and `.css` files (`src/index.html`, `src/clases.html`, `src/booking.js`, `src/styles.css`).
   - This prevents browsers from heuristically caching `booking.js` and HTML pages for days when no `Cache-Control` header is present.

2. **Long Cache TTL (`public, max-age=86400` — 1 day) for `assets/`:**
   - Configured long-lived `Cache-Control: public, max-age=86400` headers for static assets under `src/assets/` (`logo.png`, `mark.svg`).

3. **Explicit `Content-Type` Preservation (Avoiding the `binary/octet-stream` Trap):**
   - Split `aws s3 sync` into separate passes for `src/assets/` (with `--cache-control "public, max-age=86400"`) and the rest of `src/` (with `--exclude "assets/*"` and `--cache-control "public, max-age=300"`), so newly synced files receive both S3's inferred MIME type and the appropriate `Cache-Control` policy.
   - Added a per-extension `aws s3 cp ... --metadata-directive REPLACE` loop covering `html:text/html:300`, `js:application/javascript:300`, `css:text/css:300`, `png:image/png:86400`, and `svg:image/svg+xml:86400`.
   - Why this matters: `aws s3 sync` only re-uploads files whose size or mtime changed, so objects already in the bucket without `Cache-Control` wouldn't get updated headers from `sync` alone. However, running `aws s3 cp --recursive --metadata-directive REPLACE` without `--content-type` wipes out existing `Content-Type` metadata and causes S3 to reset every object to `binary/octet-stream` (making browsers download pages instead of rendering them). Pairing `--content-type` and `--cache-control` per file extension ensures both headers always travel together safely.

4. **CloudFront Invalidation:**
   - Kept the `aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths "/*"` step at the end of `scripts/deploy.sh` so edge caches drop any stale headers and serve the updated `Cache-Control` and `Content-Type` headers immediately.
