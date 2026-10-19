# Cache-Control Headers Implementation

## Summary of Changes
Updated `scripts/deploy.sh` to configure `Cache-Control` headers for all uploaded site files while preserving correct `Content-Type` headers.

### 1. Strategy
- **Short cache duration (`max-age=300`)** for code and markup (`.html`, `.js`, `.css`):
  - Prevents browsers from caching code files like `booking.js` indefinitely.
  - Ensures visitors receive updates shortly after deployment while allowing CloudFront invalidations to take effect.
- **Long cache duration (`max-age=31536000`)** for static media in `assets/` (`.png`, `.svg`):
  - Allows long-term caching for static images/assets.
- **Explicit Content-Type Preservation**:
  - Whenever updating metadata on S3 via `--metadata-directive REPLACE`, AWS S3 wipes out existing metadata if not re-specified.
  - File extension loops explicitly pass `--content-type` (`text/html`, `application/javascript`, `text/css`, `image/png`, `image/svg+xml`) alongside `--cache-control` to prevent objects from reverting to `binary/octet-stream`.

### 2. Updated Deploy Workflow in `scripts/deploy.sh`
1. `aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"`
2. Set short TTL (`max-age=300`) with explicit `Content-Type` for `html`, `js`, and `css`.
3. Set long TTL (`max-age=31536000`) with explicit `Content-Type` for `png` and `svg` under `assets/`.
4. Run CloudFront cache invalidation (`/*`).
