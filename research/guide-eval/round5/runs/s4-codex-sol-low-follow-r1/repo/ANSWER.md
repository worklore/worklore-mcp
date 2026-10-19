# Cache headers in the deploy

Updated `scripts/deploy.sh` to upload every file with an explicit `Content-Type` and `Cache-Control` header after the existing sync. HTML, JavaScript, and CSS use `public, max-age=300`; PNG and SVG files in `assets/` use `public, max-age=86400`. Unknown file types stop the deploy so they cannot silently go up without a policy.

The explicit uploads also update unchanged objects that `s3 sync` would skip. Content types are supplied with the cache policy to avoid the `binary/octet-stream` problem described in the guide. CloudFront invalidation still runs after all uploads succeed.

Verified locally with `bash -n scripts/deploy.sh` and a mocked AWS CLI that recorded the upload arguments. No deploy or external request was made. After a real deploy, check the response headers for `/`, `/booking.js`, and an asset with `curl -sI` to confirm both `Content-Type` and `Cache-Control` at the CDN.
