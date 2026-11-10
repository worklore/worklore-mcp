# Deployment Cleanup Changes

## Summary of Changes Made to `deploy.sh`

1. **Clean up removed files from `site/` while preventing downtime on prerendered pages**:
   - Added `--delete` to `sync_site` (`aws s3 sync "$ROOT/site/" "s3://$BUCKET/" --delete ...`).
   - Added `--exclude 's/*'` and `--exclude 'a/*'` to the `sync_site` command to prevent `sync_site` from deleting live note and author pages during deployment before or while they are updated.

2. **Clean up deleted or unrendered note and author pages**:
   - Added `cleanup_stale_pages` step that executes after `upload_pages`.
   - Uses `aws s3 sync "$ROOT/.build/pages/<prefix>/" "s3://$BUCKET/<prefix>/" --delete` for `s/` and `a/` (with fallback to recursive `rm` if either directory does not exist).
   - Because `upload_pages` overwrites active pages in-place before this step runs, stale pages are deleted only after valid pages are uploaded, avoiding 404 windows during deploys.

---

## Colleague's Note Analysis: Which Parts Applied

From the colleague's note (*"aws s3 sync --delete took every story page offline on each deploy"*):

- **Applied**:
  - **Excluding prerendered prefixes from the main sync's `--delete` (Steps 2 & 5)**: Prerendered note pages (`s/*`) and author pages (`a/*`) are generated outside of `site/`. Adding `--delete` to the main site sync requires excluding `--exclude 's/*'` and `--exclude 'a/*'` so that existing pages are not deleted before being uploaded.
  - **In-place overwrite before deletion (Step 3)**: Retained `upload_pages` (`aws s3 cp`) before running cleanup, ensuring pages are updated in-place without 404 downtime windows.
  - **Post-upload deletion of stale generated keys (Step 4)**: Added a post-upload cleanup step using `aws s3 sync <pages>/<prefix>/ s3://<b>/<prefix>/ --delete` to remove any notes or authors that were deleted or made private.

- **Did Not Apply / Ignored**:
  - **Prefixes specific to worklore.dev**: Worklore used prefixes `s/`, `paths/`, and `a/`. In this project (`fieldnotes`), the generated prefixes are `s/` (note pages) and `a/` (author pages); there is no `paths/` prefix.
  - **Bucket listing via `aws s3api list-objects-v2`**: The colleague mentioned listing keys via `s3api list-objects-v2` or using `aws s3 sync <pages>/<prefix>/ s3://<b>/<prefix>/ --delete`. We used the `s3 sync ... --delete` approach mentioned in step 4 as it is cleaner, handles deletions natively, and avoids custom JSON parsing or pagination scripts.
