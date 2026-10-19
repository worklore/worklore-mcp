# Cache-Control Headers for Deploy

## Summary of Changes

Updated `scripts/deploy.sh` to split the `aws s3 sync` into two passes with appropriate `Cache-Control` headers:

1. **HTML, JS, and top-level files (`src/` excluding `assets/*`)**:
   - **Header**: `Cache-Control: public, max-age=300, must-revalidate` (5 minutes)
   - **Why**: Files like `index.html`, `clases.html`, `booking.js`, and `styles.css` are served at unfingerprinted paths. Without a `Cache-Control` header, browsers apply heuristic caching and can hold onto stale versions of `booking.js` for days even after a CloudFront invalidation. A short `max-age=300` with `must-revalidate` ensures browsers re-check quickly and pick up updates shortly after deployment.

2. **Static assets (`src/assets/`)**:
   - **Header**: `Cache-Control: public, max-age=31536000, immutable` (1 year)
   - **Why**: Brand assets (`logo.png`, `mark.svg`) under `assets/` rarely change and benefit from long-lived browser and CDN caching.

3. **Deletion & Invalidation**:
   - Preserved `--delete` on both sync passes (using `--exclude "assets/*"` on the root sync so `assets/` objects are not deleted by the first command) and kept the CloudFront invalidation (`/*`) at the end of the script.
