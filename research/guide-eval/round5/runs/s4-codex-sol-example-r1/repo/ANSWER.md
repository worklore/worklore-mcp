# Deploy cache headers

Updated `scripts/deploy.sh` to set `Cache-Control: public, max-age=300` on HTML, JavaScript, CSS, and other files outside `assets/`, and `public, max-age=86400` on `assets/`. The script keeps `sync --delete`, then copies every local file so unchanged objects also receive the new metadata. It supplies explicit content types for the site's HTML, JS, CSS, PNG, and SVG files, and invalidates CloudFront after uploads finish.

The colleague's S3 and CDN case applies here: browser caches can retain an old `booking.js` after a CDN invalidation, and replacing S3 metadata without its content type can break pages. The extension-specific content types, short code cache, longer asset cache, and post-upload invalidation informed this change. The suggested S3-to-S3 `--metadata-directive REPLACE` repair does not apply: this deploy uploads local files, so it does not replace remote metadata in place. The live `curl -I` checks and fresh-browser check require a deployment and were not run.

Verified locally with `bash -n`, `git diff --check`, and a mocked AWS CLI run. The mock confirmed a deletion sync, six uploads with the expected cache policies and content types, and invalidation last. No real AWS commands were sent.
