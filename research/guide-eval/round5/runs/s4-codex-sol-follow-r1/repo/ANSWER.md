# Cache headers in the deploy

Updated `scripts/deploy.sh` to upload every file with an explicit content type and `Cache-Control` header. HTML, JavaScript (including `booking.js`), and CSS use `public, max-age=300`; files under `assets/` use `public, max-age=86400`. The script rejects unknown file types before touching the bucket, removes deleted files, and invalidates CloudFront after upload.

Uploading local files each time also updates headers on unchanged objects. The script does not use S3's `--metadata-directive REPLACE`, which could discard content types during a metadata-only copy.

Local verification passed: Bash syntax, a mocked deploy checking all six uploads and command order, rejection of an unknown file type before any AWS call, and `git diff --check`. No deployment was run. After the next authorized deploy, check `Content-Type` and `Cache-Control` on the HTML page and `/booking.js`, then load the site in a fresh browser.
