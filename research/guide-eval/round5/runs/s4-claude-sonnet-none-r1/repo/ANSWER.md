# Cache-Control on deploy

Changed `scripts/deploy.sh` (the single `aws s3 sync` is now two):

- Everything except `assets/` (HTML, `booking.js`, `styles.css`):
  `Cache-Control: public, max-age=300, must-revalidate` (5 minutes).
- `assets/`: `Cache-Control: public, max-age=31536000` (1 year).

Notes:
- `styles.css` wasn't named in the request; I put it in the short group since its
  filename isn't versioned and a stale stylesheet would have the same problem.
- Assets have a long cache but unversioned names, so if you replace `logo.png`
  in place, visitors may keep the old one for a long time. Rename the file
  (or lower the value) when changing one.
- `--exclude "assets/*"` on the first sync also stops `--delete` from touching
  assets; the second sync handles deletion there.
- Existing objects only get the header when re-uploaded. `s3 sync` skips files
  whose size/mtime are unchanged, so the first deploy may not update metadata
  for unchanged files. Force it once with `--exact-timestamps` is not enough; use
  `aws s3 cp src/ s3://BUCKET/ --recursive --cache-control ...` (or touch the files).
- Browsers that already cached `booking.js` with no header may still use their
  heuristic copy until it expires; this only fixes future loads.
- Not run: no deploy, and only `bash -n` syntax check was done.
