#!/usr/bin/env bash
# Deploy the site to S3. CI runs this on every push to main with BUCKET set.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
: "${BUCKET:?set BUCKET to the site bucket}"
export AWS_PROFILE="${AWS_PROFILE:-fieldnotes-deploy}"

build_pages() {
  echo "→ building note and author pages"
  rm -rf "$ROOT/.build/pages"
  python3 "$ROOT/build_pages.py" "$ROOT/content/stories.json" "$ROOT/.build/pages"
}

# Each sync runs with --delete so objects the build no longer produces (deleted
# or private notes, removed site/ files, authors with no public notes) are
# removed from the bucket. The two syncs are scoped so neither deletes the
# other's keys: the site sync skips the page prefixes, and the page sync only
# touches them.

sync_site() {
  echo "→ syncing site/ to s3://$BUCKET (deleting removed files)"
  aws s3 sync "$ROOT/site/" "s3://$BUCKET/" --delete \
    --exclude "s/*" --exclude "a/*" --only-show-errors
}

upload_pages() {
  # Page keys are extensionless (s/<slug>, a/<handle>), so S3 can't guess their
  # type: upload them all with text/html. Only s/ and a/ are in scope, so
  # --delete removes stale pages without touching site/ files.
  echo "→ uploading pages (deleting stale pages)"
  aws s3 sync "$ROOT/.build/pages/" "s3://$BUCKET/" --delete \
    --exclude "*" --include "s/*" --include "a/*" \
    --content-type "text/html; charset=utf-8" --cache-control "max-age=300" \
    --only-show-errors
}

build_pages
sync_site
upload_pages
echo "✓ deployed to s3://$BUCKET"
