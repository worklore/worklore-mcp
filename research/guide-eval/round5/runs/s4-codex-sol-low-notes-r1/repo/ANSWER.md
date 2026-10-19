# Cache headers for deploys

Updated `scripts/deploy.sh` to upload HTML, JavaScript, and CSS with `Cache-Control: public, max-age=300` (5 minutes). Files currently in `assets/` (`.png` and `.svg`) receive `public, max-age=86400` (1 day).

Each upload also sets its correct `Content-Type`. The script uploads these files on every deploy so unchanged objects receive the new metadata, then invalidates CloudFront as before. This prevents a metadata update from turning pages or scripts into binary downloads.

Checked shell syntax with `bash -n scripts/deploy.sh` and whitespace with `git diff --check`. No deploy was run.
