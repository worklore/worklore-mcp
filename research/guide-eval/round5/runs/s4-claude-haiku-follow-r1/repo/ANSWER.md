# Cache-Control on deploy

## What changed

`scripts/deploy.sh` now sets `Cache-Control` on every uploaded file:

| Files | Content type | Cache-Control |
|---|---|---|
| `*.html`, `*.js`, `*.css` (pages and code) | `text/html`, `application/javascript`, `text/css` (utf-8) | `public, max-age=300` |
| `assets/*.png`, `assets/*.svg` | `image/png`, `image/svg+xml` | `public, max-age=86400` |

The deploy runs in this order:

1. **Guard.** If `src/` contains a file type the script has no content type for, it exits before uploading anything.
2. **`aws s3 sync src/ --delete`.** Unchanged from before. It handles uploads and removals.
3. **Per-type `aws s3 cp` from `src/`.** `sync` skips files whose size and mtime haven't changed, so it would never add headers to objects already in the bucket. Re-uploading each type from local files, with `--content-type` and `--cache-control` stated explicitly, sets both on every object.
4. **CloudFront invalidation** for `/*`, as before.

## Why not the guide's copy-onto-self loop

The guide copies each object onto itself with `--metadata-directive REPLACE`. That replaces all metadata, and the guide's loop passes content type per extension. This script does not need that step. It uploads from the local files, so the content type and cache policy are set in the same command and nothing is replaced in place. The guard is there so a new file type cannot go out with no content type.

## Choices I made

- **CSS is short-cached.** You named HTML and JS, and `styles.css` sits at the root, not in `assets/`, so it gets the short policy alongside the code.
- **Assets get `max-age=86400`, not a year.** The asset filenames are not fingerprinted. A year would leave a changed `logo.png` stale for a year on returning visitors.
- **Charset is in the content type** (`; charset=utf-8`), because the pages are Spanish text.

## What I verified

- `bash -n` passes on the script.
- Ran the script with a stub `aws` that only prints its arguments. The sequence is correct, and the guard exits 1 when a file with an unknown extension is in `src/`. The stub and the temporary test file were removed afterwards.
- `aws s3 cp --dryrun` with the same include filters matches all six files in `src/`, including `assets/logo.png` and `assets/mark.svg`, with no misses or extras.

## What I did not verify

- **I did not deploy.** Nothing was uploaded to S3 and no CloudFront invalidation was created, per the ground rules.
- **I did not run the `curl -sI` check** from the guide. It needs the live site, so it has to run after the first real deploy:
  - `curl -sI https://<site>/ | grep -i content-type` should show `text/html`.
  - The same check on `/booking.js` should show `application/javascript`.
  - Both `cache-control` headers should match the table above.
- **The README's "Known problem" note is still accurate** until a deploy with this script runs. I left the README unchanged.

Changes are uncommitted in `scripts/deploy.sh` and `ANSWER.md`.
