# Deployment Cleanup Changes

## Problem
Previously, when a note was deleted or marked private, its prerendered page (`s/<slug>`) and potentially orphaned author pages (`a/<handle>`) remained in the S3 bucket because `deploy.sh` only ran `aws s3 sync` without `--delete` on `site/` and used `aws s3 cp` in a loop for `.build/pages`. Similarly, files removed from `site/` were never deleted from the bucket.

## Changes Made
Updated `deploy.sh`:
1. **`sync_site`**:
   - Added `--delete` to remove files from the S3 bucket that no longer exist in `site/`.
   - Added `--exclude "s/*" --exclude "a/*"` so that syncing static site assets does not prematurely delete generated note (`s/*`) or author (`a/*`) pages.
2. **`upload_pages`**:
   - Replaced individual `aws s3 cp` commands with `aws s3 sync "$ROOT/.build/pages/" "s3://$BUCKET/"` with `--delete`.
   - Used `--exclude "*" --include "s/*" --include "a/*"` to scope deletion and syncing strictly to note and author pages.
   - Retained `--content-type "text/html; charset=utf-8"` and `--cache-control "max-age=300"` for the prerendered pages.
