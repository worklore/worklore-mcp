# Answer: stale pages and files stay live after deploy

## Cause

`deploy.sh` only ever added or overwrote objects in the bucket. It runs
`aws s3 sync` (no `--delete`) for `site/` and `aws s3 cp` for the prerendered
pages. Nothing removed an object whose source had gone away, so:

- a note that was deleted or set to `private` kept its `s/<slug>` page;
- an author with no public notes left was kept at `a/<handle>`;
- a file removed from `site/` stayed in the bucket.

## Change (`deploy.sh`)

Added a `prune_bucket` step that runs after the uploads:

1. Build the expected key list: every file under `site/` plus every file under
   `.build/pages/`, with the `./` prefix stripped, sorted.
2. List every key in `s3://$BUCKET` (`aws s3api list-objects-v2`), dropping the
   literal `None` that the CLI prints for an empty bucket.
3. `comm -13` gives the keys in the bucket that the build did not produce. Each
   one is removed with `aws s3 rm`.

Design choices:

- **Prune runs last.** With `set -e`, a failed build or upload stops the script
  before anything is deleted, so a broken build cannot wipe the site.
- **Whole bucket, not just `s/` and `a/`.** The request said "anything in the
  bucket that the build no longer produces", so the check covers every key.
  Consequence: any object put in the bucket by hand, outside this repo, is
  deleted on the next deploy.
- `LC_ALL=C` is set inside the function so `sort` and `comm` agree.

## Verification

- `bash -n deploy.sh` passes.
- I ran the script against a fake `aws` CLI (a shell stub outside the repo, in a
  scratch directory, not committed). The fake bucket held the expected keys plus
  `old.html`, `s/old-note`, `s/draft-moss-survey` (private note) and `a/cy`
  (author with no notes). The run deleted exactly those four keys and left all
  expected keys alone. A rerun against an empty bucket reported "nothing stale"
  and exited 0.
- **Not tested against real S3 or CloudFront.** I did not deploy, and I had no
  AWS access. The `list-objects-v2 --query` output and the `aws s3 rm` calls
  should be checked on the first real CI run.

## Not covered

- **CloudFront cache.** The pages are served with `max-age=300`, and the script
  does not invalidate CloudFront. A deleted page can still be served from an edge
  cache until its TTL expires. Making the removal immediate needs an invalidation
  for the removed paths (`aws cloudfront create-invalidation`), which requires the
  distribution ID. I did not add it because the ID is not in the repo.
- The README still describes the deploy as "syncs and uploads". It should
  mention the prune step; I did not change it.
