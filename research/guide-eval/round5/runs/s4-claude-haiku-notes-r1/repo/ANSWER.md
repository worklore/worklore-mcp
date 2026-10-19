# Cache-Control on deploy

## What changed

`scripts/deploy.sh` now sets `Content-Type` and `Cache-Control` on every object it uploads.

- **HTML, JS, CSS** (`index.html`, `clases.html`, `booking.js`, `styles.css`): `public, max-age=300` (5 minutes).
- **`assets/`** (`logo.png`, `mark.svg`): `public, max-age=86400` (1 day).

The steps, in order:

1. Check that every file in `src/` has a known extension. If one does not (for example `favicon.ico`), the script stops before touching the bucket.
2. `aws s3 sync src/ … --delete`, as before. This removes deleted files and uploads changed ones.
3. Re-upload each file with `aws s3 cp`, passing `--content-type` and `--cache-control` explicitly.
4. Invalidate CloudFront, as before.

## Choices I made

- **Re-upload from disk, not S3 self-copy.** The notes file describes the octet-stream outage caused by `aws s3 cp --recursive --metadata-directive REPLACE` without `--content-type`. The script never uses that form. Each file is uploaded from the local copy with its type given explicitly.
- **`styles.css` is treated as short-lived.** You asked for short for HTML and JS and long for `assets/`. CSS is code that sits at the root, not under `assets/`, so it gets the short policy. Move it if you want it long.
- **Long is one day, not a year with `immutable`.** The asset filenames are not content-hashed. A year-long cache would leave an updated `logo.png` stuck on old visitors' browsers. Add hashed names before raising the TTL.
- **`charset=utf-8` added to text types.** The HTML and JS contain non-ASCII text (`ñ`, `á`, `Cerámica`), so the charset is stated explicitly.

## What I verified

- `bash -n scripts/deploy.sh` passes.
- I ran the script with a stub `aws` on `PATH` that only prints its arguments. Each file got the expected type and cache value, with each value passed as a single argument.
- A `favicon.ico` added to `src/` made the script exit with status 1 before any upload.
- I did not run the real script. Nothing was deployed, uploaded, or sent to AWS. The stub and the temporary `favicon.ico` were removed afterwards.

## What still has to happen

- **Run `./scripts/deploy.sh` once, yourself.** Existing objects in the bucket have no `Cache-Control` yet. The header pass in step 3 is what fixes them, even for files that have not changed.
- **After that deploy, check the headers.** Run `curl -sI https://<your-site>/booking.js` and confirm `cache-control: public, max-age=300` and `content-type: application/javascript; charset=utf-8`. Do the same for `/` (expect `text/html`) and for `/assets/logo.png` (expect the one-day cache). A 200 status alone does not prove the headers are right.
- **README is out of date.** Its "Known problem" paragraph still describes the missing header. I left it alone because you did not ask for it. It can be updated once the fix is confirmed live.
