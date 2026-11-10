# Changes Made

Updated [`deploy.sh`](file:///tmp/h-qqWlxw/deploy.sh) so that files deleted locally or rendered obsolete by build changes (such as deleted or privatized notes/authors, or files removed from `site/`) are removed from the destination S3 bucket.

### Details of Changes:
1. **Unified Staging (`build_site`)**:
   - Replaced `build_pages` with `build_site`, which stages all static assets from `site/` into `$ROOT/.build/site` and renders pages directly into `$ROOT/.build/site` using `build_pages.py`.
   - Ensures directories `s/` and `a/` are created inside `.build/site`.

2. **Synchronization with Deletion (`sync_bucket`)**:
   - Replaced `sync_site` and `upload_pages` with `sync_bucket` using `aws s3 sync ... --delete`.
   - The bucket is synced in three targeted steps:
     - Root static site assets: `aws s3 sync "$ROOT/.build/site" "s3://$BUCKET" --delete --exclude "s/*" --exclude "a/*" --only-show-errors` (removes deleted site assets without wiping note or author directories).
     - Note pages: `aws s3 sync "$ROOT/.build/site/s" "s3://$BUCKET/s" --delete --content-type "text/html; charset=utf-8" --cache-control "max-age=300" --only-show-errors` (deletes any removed or private note pages and maintains extensionless HTML metadata).
     - Author pages: `aws s3 sync "$ROOT/.build/site/a" "s3://$BUCKET/a" --delete --content-type "text/html; charset=utf-8" --cache-control "max-age=300" --only-show-errors` (deletes author pages for authors who no longer have public notes).
