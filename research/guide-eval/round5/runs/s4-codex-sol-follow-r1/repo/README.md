# ruta-ceramica site

Static site for a ceramics studio: plain HTML, one CSS file, one JS file
(the class booking widget). Hosted on S3 behind CloudFront.

- `src/` — the site as served (no build step; `scripts/deploy.sh` copies it up)
- `scripts/deploy.sh` — upload to the bucket and invalidate CloudFront

Deploy: `./scripts/deploy.sh` (needs AWS CLI configured with the studio profile).

The deploy gives HTML, JavaScript, and CSS a five-minute browser cache and
files under `assets/` a one-day cache. It uploads each file with an explicit
content type, removes deleted files from the bucket, then invalidates CloudFront.
