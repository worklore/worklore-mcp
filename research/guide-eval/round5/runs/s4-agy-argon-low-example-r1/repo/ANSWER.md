# Deploy Cache-Control Update (`ANSWER.md`)

## What Was Done

Updated `scripts/deploy.sh` to attach appropriate `Cache-Control` and `Content-Type` headers during deployment to S3 (`s3://ruta-ceramica-site-7f3a/`) before running the CloudFront invalidation (`E2QX9ZK1DEMO01`):

1. **Sync with path-appropriate `Cache-Control` headers:**
   - Sync top-level code/markup files (`src/` excluding `assets/*`, covering `index.html`, `clases.html`, `booking.js`, and `styles.css`) with a short cache TTL: `Cache-Control: public, max-age=300` (5 minutes).
   - Sync static assets under `src/assets/` (`logo.png`, `mark.svg`) to `s3://$BUCKET/assets/` with a long cache TTL: `Cache-Control: public, max-age=86400` (24 hours).

2. **Per-extension metadata replacement (`--metadata-directive REPLACE`) with explicit `--content-type`:**
   - Added the per-extension loop in `scripts/deploy.sh` using `aws s3 cp s3://$BUCKET/ s3://$BUCKET/ --recursive --metadata-directive REPLACE` paired with explicit `--content-type` and `--cache-control` flags (plus `--profile "$PROFILE"`):
     - `*.html` → `Content-Type: text/html`, `Cache-Control: public, max-age=300`
     - `*.js` (`booking.js`) → `Content-Type: application/javascript`, `Cache-Control: public, max-age=300`
     - `*.css` (`styles.css`) → `Content-Type: text/css`, `Cache-Control: public, max-age=300`
     - `*.png` (`assets/logo.png`) → `Content-Type: image/png`, `Cache-Control: public, max-age=86400`
     - `*.svg` (`assets/mark.svg`) → `Content-Type: image/svg+xml`, `Cache-Control: public, max-age=86400`
   - Why both `sync` and the `cp --metadata-directive REPLACE` loop? `aws s3 sync` only uploads files whose size or modification time changed, so objects already sitting in the bucket without `Cache-Control` headers would not get updated by `sync` alone. Conversely, `sync` handles uploading new/modified files and `--delete` removes stale files.

---

## Which Parts of the Colleague's Note Applied (and Which Did Not)

### Parts That Applied
- **The `--metadata-directive REPLACE` / `Content-Type` trap (Step 1 & core lesson):**
  When updating metadata on existing S3 objects (`aws s3 cp ... --metadata-directive REPLACE`), S3 replaces *all* object metadata. Omitting `--content-type` causes S3 to reset the MIME type to `binary/octet-stream`, causing browsers (especially with `nosniff`) to download pages as files or refuse to execute scripts/stylesheets instead of rendering the site.
- **Pairing `--content-type` and `--cache-control` per file extension (Step 2):**
  Looping over file extensions (`html:text/html:300`, `js:application/javascript:300`, `css:text/css:300`, `png:image/png:86400`, `svg:image/svg+xml:86400`) ensures short TTLs (`max-age=300`) for HTML/JS/CSS and long TTLs (`max-age=86400`) for `assets/` (`logo.png`, `mark.svg`), while guaranteeing that `Content-Type` and `Cache-Control` always travel together.
- **CloudFront CDN invalidation after setting headers (Step 3):**
  CloudFront caches response headers at the edge alongside object bodies, so `aws cloudfront create-invalidation` must run *after* the S3 upload and metadata updates. `scripts/deploy.sh` already had the invalidation command; we ensured it runs after all header updates complete.
- **Putting the logic into `scripts/deploy.sh` (Step 4):**
  Rather than treating header updates as a one-off shell command, the header assignment and per-extension loop were placed directly in `scripts/deploy.sh` (with `--profile "$PROFILE"` matching the existing script).

### Parts That Did Not Apply / Were Ignored
- **Asking the user for bucket name, CDN distribution ID, and asset paths ("Your agent will need from you..."):**
  All of this information was already present in the repository (`BUCKET="ruta-ceramica-site-7f3a"`, `DISTRIBUTION_ID="E2QX9ZK1DEMO01"`, `PROFILE="studio"` in `scripts/deploy.sh`, and the directory layout in `src/` and `src/assets/`).
- **Running live AWS CLI commands against S3/CloudFront or curling the live site ("Prerequisites" & "Verify" sections):**
  Per the ground rules ("work only inside the current directory. Do not deploy, publish, submit or report anything to any external service"), we only modified the local repository (`scripts/deploy.sh` and `ANSWER.md`) and did not execute a live deploy or network calls.
