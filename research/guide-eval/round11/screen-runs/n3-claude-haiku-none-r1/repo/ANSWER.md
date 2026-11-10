# Answer: deploy.sh now removes stale files from the bucket

## The problem
- `sync_site` ran `aws s3 sync site/ s3://$BUCKET/` without `--delete`, so a file removed from `site/` stayed in the bucket.
- `upload_pages` only ran `aws s3 cp` for pages that are currently built. Nothing removed page keys for deleted or private notes, or for authors with no public notes left, so those pages stayed live.

## The change (`deploy.sh`)
1. **`sync_site`** now passes `--delete`, so bucket files that are no longer in `site/` are removed. It also passes `--exclude "s/*" --exclude "a/*"`, so the sync never touches generated pages. S3 sync applies filters to the destination side too, which is what keeps page keys from being deleted here.
2. **New `prune_pages` step** (runs after `upload_pages`). It lists the keys under `s/` and `a/` in the bucket, compares them with the files in `.build/pages`, and runs `aws s3 rm` on any key the build did not produce. Only those two prefixes are considered.
3. **`build_pages`** now runs `mkdir -p .build/pages`, so an empty build (no public notes) produces an empty directory instead of an error. That lets the prune step remove every page.

Safety properties:
- If the listing fails, `set -e` stops the script before any delete. I checked this.
- If the build fails, the script stops before the sync and prune steps.
- Pages are still uploaded with `text/html; charset=utf-8`, as before.

## Also changed
- `README.md`: one paragraph describing the new deletion behaviour.

## How I verified it
I did **not** deploy and did not touch any real bucket or AWS account. I ran `deploy.sh` with a stub `aws` on PATH that logged its calls and answered listings from a fake bucket:
- Normal run: the real `build_pages.py` built 3 public notes and 2 authors. The stale page keys `s/draft-moss-survey` (private), `s/old-deleted-note` (deleted) and `a/carol` (no public notes) were removed. Live pages were kept. The sync ran with `--delete` and the page-prefix excludes.
- Empty build (all notes private): the orphaned `s/gone` was removed. The `None` line that `--output text` prints for an empty listing was ignored.
- Failing listing: the script exited 1 and issued no `aws s3 rm`.

The stub and test directories were deleted afterwards. The change is not committed.

## Not verified
- The real `aws s3 sync --delete` filter behaviour (that `--exclude` protects destination-only keys). I relied on the documented AWS CLI behaviour that filters apply to both sides. A dry run against the real bucket, e.g. `aws s3 sync ... --dryrun --delete`, would confirm it. Running that is your call, since it touches the real bucket.
- Permissions: the deploy role needs `s3:ListBucket` (for `list-objects-v2`) and `s3:DeleteObject` in addition to what it already had.
- CloudFront may still serve cached copies of removed pages until the cache expires or an invalidation is issued. The script does not invalidate the distribution, and I did not add that.
