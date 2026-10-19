# Cache-Control on deploy

## What changed

`scripts/deploy.sh` now uploads every file with an explicit **Content-Type and
Cache-Control together**, from a single per-extension table:

| Files                         | Content-Type                            | Cache-Control            |
|-------------------------------|-----------------------------------------|--------------------------|
| `*.html` (outside `assets/`)  | `text/html; charset=utf-8`              | `public, max-age=300`    |
| `*.js`   (outside `assets/`)  | `application/javascript; charset=utf-8` | `public, max-age=300`    |
| `*.css`  (outside `assets/`)  | `text/css; charset=utf-8`               | `public, max-age=300`    |
| `assets/*.png`                | `image/png`                             | `public, max-age=86400`  |
| `assets/*.svg`                | `image/svg+xml`                         | `public, max-age=86400`  |

With a 5-minute max-age, returning visitors re-check `booking.js` within
minutes of a deploy instead of holding the old copy for days.

Order of the deploy:
1. **Coverage guard** — if any file in `src/` has no rule in the table, the
   script stops before uploading anything (so a new `.txt`/`.woff2` can't go
   up with a guessed type or no cache policy). Add a line to `RULES` for it.
2. **Upload** — one `aws s3 cp src/ … --recursive` per rule, from local files,
   with both `--content-type` and `--cache-control`.
3. **Delete stale objects** — `aws s3 sync --delete --size-only`. Everything
   was just uploaded, so this only deletes and never re-uploads without headers.
4. **Read the headers back** — `head-object` on `index.html`, `booking.js`,
   `styles.css` and `assets/logo.png`; the deploy fails if Content-Type or
   Cache-Control isn't what's expected.
5. **CloudFront invalidation** `/*` (as before) — the edge holds the old,
   header-less copies too.

## Why not the one-liner

I deliberately did **not** fix the existing objects with
`aws s3 cp s3://$BUCKET/ s3://$BUCKET/ --recursive --metadata-directive REPLACE --cache-control …`.
`REPLACE` replaces *all* metadata, including Content-Type; without
`--content-type` every object becomes `binary/octet-stream` and the site stops
rendering while every request still returns 200. Instead, the next normal
deploy re-uploads every file from `src/` with correct headers, so no separate
"fix the bucket" step is needed.

## Verification

- Not deployed and nothing sent to AWS (per the ground rules).
- Dry run with a stub `aws` that emulates the CLI's include/exclude ordering:
  all 6 files got exactly the type/cache pair in the table above, none was
  uploaded twice, the header read-back passed, and adding an uncovered
  `src/robots.txt` made the script abort before any upload. Stub removed afterwards.

**After you run the real deploy**, check (a 200 alone proves nothing):

```
curl -sI https://<site>/           | grep -i -E 'content-type|cache-control'   # text/html, max-age=300
curl -sI https://<site>/booking.js | grep -i -E 'content-type|cache-control'   # application/javascript, max-age=300
curl -sI https://<site>/assets/logo.png | grep -i cache-control                # max-age=86400
```

Then open the site in a private window / browser that has never seen it.

## Notes / choices you may want to revisit

- **Assets are 1 day, not a year.** Filenames in `assets/` aren't fingerprinted
  (`logo.png`, not `logo.3f9a.png`), so a year-long `immutable` would pin a
  changed logo in browsers for a year. If you start hashing asset names, raise
  `LONG` to `public, max-age=31536000, immutable`.
- **Visitors who already have the old `booking.js`** cached with no header
  will let it expire by their browser's heuristic; this deploy can't reach
  copies already in browsers. From the first deploy onward, it's ≤5 minutes.
- If you want HTML always re-validated, set it to `no-cache` instead of
  `max-age=300` (one-line change in the script).
