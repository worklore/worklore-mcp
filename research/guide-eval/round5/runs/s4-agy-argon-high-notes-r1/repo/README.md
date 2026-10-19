# ruta-ceramica site

Static site for a ceramics studio: plain HTML, one CSS file, one JS file
(the class booking widget). Hosted on S3 behind CloudFront.

- `src/` — the site as served (no build step; `scripts/deploy.sh` copies it up)
- `scripts/deploy.sh` — upload to the bucket and invalidate CloudFront

Deploy: `./scripts/deploy.sh` (needs AWS CLI configured with the studio profile).

Known problem: after a deploy, returning visitors keep running the old
`booking.js` for days. The CloudFront invalidation runs every time, but
browsers never ask again, because the objects are uploaded with no
`Cache-Control` header at all.
