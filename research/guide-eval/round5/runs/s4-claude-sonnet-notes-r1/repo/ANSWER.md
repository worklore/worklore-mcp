# Cache-Control on deploy

Changed `scripts/deploy.sh` (not run; nothing was deployed).

- The single `aws s3 sync` is replaced by per-extension syncs that set `--cache-control` and an explicit `--content-type` together.
- HTML, JS, CSS: `public, max-age=300` (5 minutes), so a new `booking.js` reaches browsers quickly.
- `assets/` (png, svg): `public, max-age=2592000` (30 days).
- Content types are explicit (`text/html`, `application/javascript`, `text/css`, `image/png`, `image/svg+xml`). This avoids the `binary/octet-stream` trap described in `notes/a-cache-header-tweak-served-my-whole-site-as-octet-stream.md`. I did not use `--metadata-directive REPLACE`.
- The script fails early if `src/` contains a file type with no mapping.
- `--delete` still works, applied per pass within each file type.
- The CloudFront invalidation is unchanged.

Notes:
- Assets aren't fingerprinted, so a replaced `logo.png` can stay cached up to 30 days. Rename the file or shorten `LONG` if that matters.
- Visitors who already cached the old `booking.js` with no header keep it until their browser revalidates. The new headers only apply after the next deploy.
- After deploying, check with `curl -sI <site>/booking.js`. It should show `content-type: application/javascript` and the `cache-control` header.
