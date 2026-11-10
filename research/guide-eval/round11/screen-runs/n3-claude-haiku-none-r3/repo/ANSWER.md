# Answer: remove stale objects on deploy

## Problem

`deploy.sh` only ever copied files into the bucket. Nothing removed an object
whose source had gone away, so:

- a note that was deleted or made `private` kept its `s/<slug>` page, because
  `build_pages.py` no longer writes it but the old object was still in S3;
- an author with no public notes kept `a/<handle>`;
- a file removed from `site/` stayed in the bucket.

## Change

**`deploy.sh`**

- `sync_site` now runs `aws s3 sync site/ s3://$BUCKET/ --delete`, with
  `--exclude "s/*" --exclude "a/*"` so this step never deletes page keys.
- `upload_pages` replaces the per-file `aws s3 cp` loop with
  `aws s3 sync .build/pages/ s3://$BUCKET/ --delete`, restricted to
  `--exclude "*" --include "s/*" --include "a/*"`. That scope means it only
  creates, updates or deletes page keys, never `site/` files.
- The page sync keeps the same headers as before: `Content-Type: text/html;
  charset=utf-8` (needed because the keys have no extension) and
  `Cache-Control: max-age=300`.
- The build still runs first and `set -e` still applies, so a failed build
  stops the deploy before anything is deleted.

**`build_pages.py`**

- Calls `os.makedirs(out, exist_ok=True)` up front. Without this, when no
  notes are public the output directory is never created and the `aws s3 sync`
  source path does not exist. (The old per-file loop tolerated that case; sync
  does not.)

## Verification

I could not test against a real bucket. The README says there is no test
bucket, and I was not allowed to deploy. What I did check locally:

- Ran `deploy.sh` with `BUCKET=test-bucket` and a stub `aws` on `PATH` that
  only logs its arguments. The build output was correct (3 notes, 2 authors,
  the private note excluded), and both sync commands had the expected flags
  and filters.
- Ran `build_pages.py` with every note set to private. It exits cleanly and
  creates an empty output directory, so the sync would delete all `s/` and `a/`
  keys, which is the intended result.
- I did not verify S3's filter behaviour (exclude and include combined with
  `--delete`) against live S3. The AWS CLI documents that files excluded by
  filters are not deleted, and that is what the scoping relies on. Check it on
  the first CI run, or with `aws s3 sync --dryrun` against a bucket you own.

## Things to know before merging

- **`--delete` on the site sync removes anything in the bucket root that is not
  in `site/` or `.build/pages`.** Any file uploaded by hand, or by another
  process, will be deleted on the next push to main.
- **CloudFront still serves cached copies.** Deleting an object from S3 does
  not purge the CDN. A removed page can stay live at the edge until its TTL
  expires (`max-age=300` on pages). For immediate removal, add a CloudFront
  invalidation for the deleted paths. I did not add one because it needs the
  distribution ID and is an action on an external service.
- Changes are uncommitted in the working tree.
