# Deploy Cache-Control Headers Configuration

## Summary of Changes

Updated [`scripts/deploy.sh`](scripts/deploy.sh) to apply differentiated `Cache-Control` headers during deployment:

1. **Static Assets (`src/assets/`)**:
   - Synchronized to `s3://$BUCKET/assets/` with a long cache lifetime:
     `--cache-control "public, max-age=31536000, immutable"` (1 year, immutable).
   - This ensures media assets like images/SVGs are cached aggressively by both CloudFront and browsers.

2. **HTML and JavaScript files (`src/`)**:
   - Synchronized to `s3://$BUCKET/` excluding `assets/*` with a short cache lifetime:
     `--cache-control "public, max-age=0, must-revalidate"`.
   - Combined with `--delete` to remove removed files on the bucket.
   - This ensures browsers revalidate HTML pages and [`booking.js`](src/booking.js) immediately rather than serving stale versions for days after new deployments.
