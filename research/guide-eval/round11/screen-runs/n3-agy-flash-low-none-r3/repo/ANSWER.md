# Changes to deploy.sh

To ensure that deleting or making a note private removes obsolete note/author pages from the S3 bucket, and that removing files from `site/` removes them from the bucket:

1. Added an `assemble_site` step in `deploy.sh` that aggregates the static assets from `site/` and the prerendered HTML pages from `.build/pages/` into `.build/site/`.
2. Updated `sync_site` to sync `.build/site/` to `s3://$BUCKET/` with the `--delete` flag. This removes any objects from the bucket that no longer exist in either `site/` or `.build/pages/`.
3. Retained `upload_pages` following the sync step to ensure all extensionless note and author pages are uploaded with the required `text/html; charset=utf-8` MIME type and `Cache-Control` settings.
