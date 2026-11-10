# S3 Deployment and Cleanup Updates

## Summary of Changes

To ensure that deleted/private notes and deleted files from `site/` are removed from the S3 bucket without causing downtime for existing note and author pages during deploys, `deploy.sh` was updated with the following changes:

1. **Clean up removed files from `site/` while protecting generated pages (`sync_site`):**
   - Added `--delete` to `aws s3 sync "$ROOT/site/" "s3://$BUCKET/"` so that files removed from `site/` are pruned from the bucket.
   - Added `--exclude "s/*" --exclude "a/*"` to the sync command. This prevents `sync_site` from deleting prerendered note (`s/<slug>`) and author (`a/<handle>`) pages before the upload step, avoiding 404 errors during deploy.

2. **Preserve zero-downtime page updates (`upload_pages`):**
   - Kept `aws s3 cp` in `upload_pages` so that existing prerendered pages are updated in place with their required `text/html; charset=utf-8` content type.

3. **Prune stale generated pages (`clean_stale_pages`):**
   - Added a cleanup step executed after `upload_pages`:
     ```bash
     aws s3 sync "$ROOT/.build/pages/s/" "s3://$BUCKET/s/" --delete --only-show-errors
     aws s3 sync "$ROOT/.build/pages/a/" "s3://$BUCKET/a/" --delete --only-show-errors
     ```
   - This compares the newly built pages in `.build/pages/s/` and `.build/pages/a/` against S3 and deletes any keys in the bucket that the current build no longer produces (e.g. when a note is deleted or set to private, or an author has no public notes remaining).

---

## Colleague Note: Applicable vs. Non-Applicable Parts

### Parts that applied:
- **Prefix exclusion from main sync:** Excluding generated prefixes (`s/*` and `a/*`) from the main `aws s3 sync ... --delete` command prevents prerendered pages from being deleted during the shell sync.
- **In-place overwrite:** Retaining `upload_pages` with `aws s3 cp` ensures live pages stay reachable until new content is uploaded.
- **Post-upload prefix sync with `--delete`:** Using `aws s3 sync <pages-dir>/<prefix>/ s3://<bucket>/<prefix>/ --delete` after the upload step reliably cleans up stale notes and author pages without needing custom bucket listing scripts.
- **Pruning static shell files:** Enabling `--delete` on the `site/` sync ensures files removed from `site/` are removed from the bucket.

### Parts that did not apply:
- **Worklore-specific paths:** The colleague's note referenced paths like `paths/` and the Worklore site structure. In this project (`fieldnotes`), the generated prefixes are `s/` (stories) and `a/` (authors).
- **Listing via `aws s3api list-objects-v2`:** The colleague mentioned listing prefixes via `s3api list-objects-v2` as an alternative to `sync --delete`. Running `aws s3 sync ... --delete` per prefix after upload is cleaner, simpler, and directly supported by the AWS CLI.
