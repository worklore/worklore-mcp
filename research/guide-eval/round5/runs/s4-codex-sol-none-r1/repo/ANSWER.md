# Cache headers for the site deploy

Updated `scripts/deploy.sh` to upload root site files, including HTML and
`booking.js`, with `Cache-Control: public, max-age=300, must-revalidate`
(five minutes). Files under `assets/` receive
`Cache-Control: public, max-age=31536000` (one year).

The deploy still syncs with `--delete`, then re-uploads both cache classes so
unchanged S3 objects also receive the new headers. CloudFront invalidation
still runs after the uploads. No deployment was run.
