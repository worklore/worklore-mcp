# Removing stale pages and files on deploy

## The problem

`deploy.sh` never removed anything from the bucket. The `site/` sync had no
`--delete`, so a deleted or private note kept its page, and a file removed from
`site/` stayed too.

## What changed (`deploy.sh`)

Each deploy now runs these steps in order:

1. **Build** the pages into `.build/pages` (unchanged, plus a `mkdir -p` so an
   empty build, with every note private, doesn't break the later steps).
2. **Sync `site/` with `--delete`**, with `--exclude <prefix>/*` for each page
   prefix the build produced. Files removed from `site/` are deleted. Pages are
   never in the sync's scope, so they aren't deleted and re-uploaded.
3. **Upload each page in place** with `aws s3 cp` to the same key, as before.
   The old copy keeps serving until the new one replaces it.
4. **Remove stale pages.** For each page prefix, list the bucket keys with
   `s3api list-objects-v2`, subtract the keys this build produced (`comm -23`),
   and `delete-object` the rest.

The page prefixes are read from the build's output folders (`s`, `a`), not
hard-coded, so a new prefix is covered without editing the deploy script.

## Why the exclusion is needed

Adding `--delete` without the exclusion would have caused the outage the colleague
note describes. The page keys are not in `site/`, so the sync would delete every
page on each deploy, and the uploads would bring them back one at a time, with
404s in between. The exclusion closes that gap.

## What from the colleague's note applied

- **Exclude generated keys from the `--delete` sync:** applied. The exclusions
  come from the build's page prefixes.
- **Upload as an overwrite in place:** already the case (`cp` to the same key),
  kept as is.
- **Remove stale pages after the upload by listing the bucket:** applied, as step
  4. I used `list-objects-v2` plus `delete-object` instead of a second
  `sync --delete`, so the deletes only touch keys under page prefixes.
- **Keep removing files from `site/` with the main sync's `--delete`:** applied.

What did not apply: the worklore-specific prefixes (`paths/`, the slugs), the
2026-10-15 date, the Google test, and the curl-every-second check. That check
needs a live deploy, and I was not allowed to deploy. The outage in the note was
caused by a `--delete` sync that this repo didn't have yet. The point that carried
over is the exclusion, which I added before introducing `--delete`.

## Verification

- `bash -n deploy.sh` passes.
- I ran `deploy.sh` under `/bin/bash` (3.2, the macOS default) against a fake
  `aws` CLI outside the repo, with a fixed bucket listing. Nothing touched real
  S3. The commands came out as intended:
  - the sync used `--delete --exclude a/* --exclude s/*`;
  - all three public pages and both authors were uploaded with `text/html`;
  - `s/draft-moss-survey` (private), `s/bird-calls-at-dawn-old` and
    `a/gone-author` (not produced by the build) were deleted;
  - `s/tide-tables-offline` and `a/ann` (live) were not deleted.
- **Not verified:** the real behavior of `--exclude` against the real bucket. I
  believe the AWS CLI applies `--exclude` to destination keys when `--delete` is
  set, which is what makes this work. Before the first live deploy, check it with
  a read-only dry run:
  `aws s3 sync site/ s3://<bucket>/ --delete --exclude 's/*' --exclude 'a/*' --dryrun`
  The output should list no `delete:` lines for `s/` or `a/` keys.
- **Not verified:** a live deploy. Per the ground rules I did not deploy, so the
  "every page answers 200 during a deploy" check is still to run.

## Behavior to be aware of

- The sync now deletes **every** bucket key that is not in `site/` and not under
  a page prefix of the current build. The bucket is assumed to hold only the site
  and its pages. Anything uploaded to the bucket by hand will be removed on the
  next deploy.
- If the build stops producing a prefix entirely (for example, all notes in `s/`
  become private), that prefix is no longer excluded, so the sync removes its old
  keys. That is the intended result.
