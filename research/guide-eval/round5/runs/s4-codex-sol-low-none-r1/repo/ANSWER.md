Updated `scripts/deploy.sh` to set `Cache-Control` on every deploy:

- HTML, JavaScript, and other files outside `assets/`: `public, max-age=300` (5 minutes).
- Files under `assets/`: `public, max-age=2592000` (30 days).

The deploy still syncs with `--delete` and invalidates CloudFront. It then re-uploads files with the appropriate header, including unchanged objects that need their existing metadata updated. No deploy was run.
