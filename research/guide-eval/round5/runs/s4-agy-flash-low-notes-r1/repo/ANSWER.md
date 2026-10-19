# Solution: Add Cache-Control Headers to Deploy

## Summary of Changes

To prevent browsers from holding onto outdated files such as `booking.js` while maintaining aggressive caching for static media assets, we updated [`scripts/deploy.sh`](file:///tmp/h-w62xxc/scripts/deploy.sh).

### Implementation Details
Following the documented pattern in [`notes/a-cache-header-tweak-served-my-whole-site-as-octet-stream.md`](file:///tmp/h-w62xxc/notes/a-cache-header-tweak-served-my-whole-site-as-octet-stream.md):
- When replacing S3 metadata (`--metadata-directive REPLACE`), S3 wipes existing metadata unless explicitly passed. To prevent objects from being served as `binary/octet-stream`, both `--content-type` and `--cache-control` are specified together per file type.
- Added a loop after `aws s3 sync`:
  - **Short cache duration (300 seconds / 5 minutes)**: Applied to HTML, JS, and CSS files (`.html`, `.js`, `.css`) with `public, max-age=300`.
  - **Long cache duration (86400 seconds / 1 day)**: Applied to assets (`.png`, `.svg`) with `public, max-age=86400`.
- Profile (`--profile "$PROFILE"`) is passed to all AWS CLI calls.
