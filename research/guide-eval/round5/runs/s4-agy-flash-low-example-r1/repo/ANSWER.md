# Solution: Cache-Control Headers for Deploy

## Summary of Changes

To prevent browsers from caching `booking.js` and other HTML/code files for extended periods while keeping static media assets cached long-term, [scripts/deploy.sh](file:///tmp/h-Ikbs5K/scripts/deploy.sh) was updated with the following:

1. **Retained the initial `aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"`**:
   - Ensures new and modified local files are synced and deleted files are removed from the bucket.

2. **Added short `Cache-Control` loop for HTML, JS, and CSS**:
   - Files matching `*.html`, `*.js`, and `*.css` outside `assets/` have their metadata replaced with:
     - `Cache-Control: public, max-age=300` (5 minutes)
     - Explicit `--content-type` set per extension (`text/html`, `application/javascript`, `text/css`) to avoid AWS S3 resetting the Content-Type to `binary/octet-stream`.

3. **Added long `Cache-Control` loop for `assets/`**:
   - Static asset files under `assets/` (e.g. `*.png`, `*.svg`) have their metadata replaced with:
     - `Cache-Control: public, max-age=31536000, immutable` (1 year)
     - Explicit `--content-type` (`image/png`, `image/svg+xml`).

4. **Retained CloudFront Invalidation**:
   - Invalidation on `/*` runs after the metadata updates to flush CDN edge caches immediately.

---

## Colleague's Note: What Applied and What Was Ignored

### What Applied:
- **Never run `aws s3 cp --recursive --metadata-directive REPLACE` without `--content-type`**: Because replacing metadata without supplying `--content-type` defaults/overwrites the MIME type to `binary/octet-stream`, which causes browsers to prompt downloads instead of executing JavaScript or rendering HTML.
- **Set headers per file extension with matched Content-Type and Cache-Control**: Pairing extension, Content-Type, and TTL in a loop guarantees content-type safety alongside caching policies.
- **Embed the metadata update loop into `scripts/deploy.sh`**: Ensures deploy operations are automated and reproducible, avoiding ad-hoc CLI errors.
- **Run CloudFront CDN invalidation afterwards**: Invalidation ensures edge caches fetch fresh metadata and headers.

### What Was Ignored / Adjusted:
- **Single flat loop across the entire bucket**: The colleague's snippet used a single loop targeting the root bucket for all extensions without distinguishing between code files and assets. In our setup, short cache headers (`max-age=300`) apply to code/markup (`html`, `js`, `css`), while long cache headers (`max-age=31536000, immutable`) apply specifically to `assets/` (PNG, SVG).
- **Manual one-off S3 self-copy command in the shell**: Instead of running one-off copy commands directly against the bucket, the logic was incorporated directly into the deployment script.
