# Cache headers in the deploy

Updated `scripts/deploy.sh` to upload every source file with an explicit `Content-Type` and `Cache-Control` header. HTML, JavaScript, and CSS use `public, max-age=300` (five minutes). Files under `assets/` use `public, max-age=31536000` (one year). The existing CloudFront invalidation still runs after the uploads. The initial sync still removes deleted files; the following uploads also update metadata on unchanged files.

From the colleague's note, the relevant points were that browser caches outlive CDN invalidations, metadata changes must preserve content types, and the fix belongs in the deploy script. This deploy uploads local files with explicit types rather than copying S3 objects onto themselves with `--metadata-directive REPLACE`. The suggested per-extension handling and post-upload invalidation also apply.

Verified the script with `bash -n`. No deployment or live header check was performed. After an authorized deploy, check `Content-Type` and `Cache-Control` on an HTML page, `/booking.js`, and an `assets/` file. Asset URLs are not fingerprinted, so changing an asset at the same URL can leave it stale in browsers for up to a year.
