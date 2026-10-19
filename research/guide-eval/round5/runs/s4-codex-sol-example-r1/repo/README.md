# ruta-ceramica site

Static site for a ceramics studio: plain HTML, one CSS file, one JS file
(the class booking widget). Hosted on S3 behind CloudFront.

- `src/` — the site as served (no build step; `scripts/deploy.sh` copies it up)
- `scripts/deploy.sh` — upload to the bucket and invalidate CloudFront

Deploy: `./scripts/deploy.sh` (needs AWS CLI configured with the studio profile).

The deploy sets a five-minute browser cache for HTML, JavaScript, CSS, and
other root files, and a one-day cache for `assets/`. It refreshes object
metadata even when file contents have not changed, then invalidates CloudFront.
