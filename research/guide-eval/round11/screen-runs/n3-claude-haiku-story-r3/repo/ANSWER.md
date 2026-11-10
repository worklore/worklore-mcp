# Answer: stale pages and files were never removed from the bucket

## What was wrong

`deploy.sh` had no cleanup at all:

- `aws s3 sync site/ s3://$BUCKET/` ran without `--delete`, so a file removed
  from `site/` stayed in the bucket.
- The pages were uploaded with `aws s3 cp` in a loop, which only adds or
  overwrites keys. A note that was deleted or made private (no longer in
  `content/stories.json` as public) kept its `s/<slug>` page, and an author with
  no public notes kept its `a/<handle>` page, indefinitely.

## What I changed (`deploy.sh` only)

1. **`sync_site`** still syncs `site/`, but without `--delete`. The bucket also
   holds page keys, so a `--delete` sync of the bucket root would remove them.
   Removing stale site files moved to step 4.
2. **`upload_pages`** is unchanged in behavior. Each page is written with
   `cp` to its own key, which overwrites the live page in place. A page is
   never missing during the deploy.
3. **New `prune_stale`** runs after the uploads. It:
   - builds the expected key set: every file in `site/` plus every file in
     `.build/pages/`, sorted with `LC_ALL=C`;
   - aborts if that set is empty, so a broken build cannot empty the bucket;
   - lists every key in the bucket with `aws s3api list-objects-v2`;
   - deletes the keys that are in the bucket but not in the expected set
     (`comm -23`), with `aws s3 rm`.

   Because this is a whole-bucket prune, it covers both cases: stale pages
   (deleted or private notes, authors with no notes) and files removed from
   `site/`.
4. A temp directory (`$TMP`) is created and removed on exit via `trap`.

The order is build, sync `site/`, upload pages, prune. The prune only runs after
every upload has succeeded (`set -euo pipefail`), so a failed build or upload
leaves the bucket as it was.

## Verification

I did not deploy and did not touch any real bucket. Instead:

- `bash -n deploy.sh` passes. `shellcheck` is not installed here.
- I ran `deploy.sh` against a mock `aws` on `PATH`. The mock backs the bucket
  with a local directory, rejects any `sync --delete`, and logs every call.
  The bucket started with live pages, stale pages (a deleted note, a note that
  is now private, an author with no notes), a removed `site/` file, and a stray
  root file. Results:
  - Final bucket: exactly the site files plus the live pages. The deleted,
    private, and author-less pages and the removed `old/gone.css` were removed.
  - Operation order: all `sync` and `cp` calls came before any `rm`. Live pages
    were overwritten, never deleted, so there is no window where they 404.
  - Pages were uploaded with `Content-Type: text/html; charset=utf-8`, as before.
- With the listing forced to fail, the script exited 255 and deleted nothing
  (a stray file survived).

Not verified: real AWS behavior. The mock covers the script's logic, not the
CLI itself. The `aws` commands used (`s3 sync`, `s3 cp`, `s3api
list-objects-v2 --query 'Contents[].Key' --output text`, `s3 rm`) are standard
CLI forms, and `list-objects-v2` paginates automatically. I expect an empty
bucket to list as `None`, which the script handles. A dry run against a test
bucket would confirm this, and I did not run one because the ground rules say
not to deploy.

## Limitations

- The key listing uses `--output text` and splits on tabs and newlines, so a key
  containing whitespace or a newline would be mishandled. The current slugs
  and handles don't contain either.
- A note that goes private stays live until the next deploy. That is inherent
  to a deploy-based cleanup.

## Colleague's note: what applied

- **Applied:** the core principle, that a `--delete` sync must not cover keys
  another step uploads. I took the sync's `--delete` out instead of excluding
  the page prefixes, so the sync can no longer remove them.
- **Applied:** the upload stays an in-place overwrite (`cp` to the same key),
  so the old page is served until the new one replaces it.
- **Applied:** a separate prune step after the upload removes stale keys. It
  lists the bucket and deletes what this build did not produce.
- **Applied in spirit:** the site's own `--delete` cleanup moved to the same
  prune step, because excluding page keys from the sync would have depended on
  filter semantics I could not test here.
- **Not applied:** the `--exclude 's/*'` / `--exclude 'a/*'` filters. The
  prune covers the stale-page case without them.
- **Not applied:** the `sync <pages>/s/ --delete` alternative for pruning. I
  used the list-and-compare prune, which covers every prefix and avoids
  depending on `sync --delete` behavior for extensionless keys.
- **Not applied:** the verification by polling story URLs during a deploy and
  checking for 404s. It needs a live deploy, which I did not run.
- **Not applicable:** the worklore-specific prefixes (`s/`, `paths/`, `a/`).
  This repo only has `s/` and `a/`, and the prune covers any prefix anyway.
  The worklore incident details and the Google test date are context only.
