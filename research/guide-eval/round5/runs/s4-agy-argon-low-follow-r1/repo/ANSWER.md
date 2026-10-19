# Cache-Control Headers Added to Deploy Script

## Summary of Changes

Updated [`scripts/deploy.sh`](file:///tmp/h-M5F237/scripts/deploy.sh) to set explicit `Cache-Control` and `Content-Type` metadata headers on S3 objects after `aws s3 sync` and before the CloudFront invalidation.

### Why `--content-type` is Required with `--metadata-directive REPLACE`
Running `aws s3 cp --recursive --metadata-directive REPLACE` without specifying `--content-type` overwrites **all** object metadata, resetting `Content-Type` to `binary/octet-stream`. That causes browsers to download HTML, JS, and CSS files instead of rendering/executing them.

### Per-Extension Configuration Applied
In `scripts/deploy.sh`, after syncing `src/` to `s3://$BUCKET/`, a loop iterates over each file extension and runs `aws s3 cp` onto the bucket with `--metadata-directive REPLACE`, pairing the exact MIME type with the appropriate cache TTL:

| Extension | `Content-Type` | `Cache-Control` | Target Files |
| :--- | :--- | :--- | :--- |
| `.html` | `text/html` | `public, max-age=300` (5 min) | `index.html`, `clases.html` |
| `.js` | `application/javascript` | `public, max-age=300` (5 min) | `booking.js` |
| `.css` | `text/css` | `public, max-age=300` (5 min) | `styles.css` |
| `.png` | `image/png` | `public, max-age=86400` (1 day) | `assets/logo.png` |
| `.svg` | `image/svg+xml` | `public, max-age=86400` (1 day) | `assets/mark.svg` |

After the metadata update loop completes, the CloudFront invalidation (`aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths "/*"`) runs so edge caches pick up both the updated files and the new headers.

### Verification Steps (Post-Deploy)
When deployed to production, verify that both `Content-Type` and `Cache-Control` headers are served properly (and not `binary/octet-stream`):

```bash
curl -sI https://your-site/ | grep -iE 'content-type|cache-control'
# Expected: content-type: text/html, cache-control: public, max-age=300

curl -sI https://your-site/booking.js | grep -iE 'content-type|cache-control'
# Expected: content-type: application/javascript, cache-control: public, max-age=300
```
