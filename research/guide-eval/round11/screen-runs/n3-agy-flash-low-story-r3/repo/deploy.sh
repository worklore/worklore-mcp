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

sync_site() {
  echo "→ syncing site/ to s3://$BUCKET"
  aws s3 sync "$ROOT/site/" "s3://$BUCKET/" --delete --exclude 's/*' --exclude 'a/*' --only-show-errors
}

upload_pages() {
  # Page keys are extensionless (s/<slug>, a/<handle>), so S3 can't guess their
  # type: upload each one with text/html.
  echo "→ uploading pages"
  ( cd "$ROOT/.build/pages" && find . -type f | sed 's|^\./||' | sort | while read -r key; do
      aws s3 cp "$key" "s3://$BUCKET/$key" --content-type "text/html; charset=utf-8" \
        --cache-control "max-age=300" --only-show-errors
    done )
}

cleanup_stale_pages() {
  echo "→ cleaning up stale note and author pages"
  if [ -d "$ROOT/.build/pages/s" ]; then
    aws s3 sync "$ROOT/.build/pages/s/" "s3://$BUCKET/s/" --delete --only-show-errors
  else
    aws s3 rm "s3://$BUCKET/s/" --recursive --only-show-errors
  fi
  if [ -d "$ROOT/.build/pages/a" ]; then
    aws s3 sync "$ROOT/.build/pages/a/" "s3://$BUCKET/a/" --delete --only-show-errors
  else
    aws s3 rm "s3://$BUCKET/a/" --recursive --only-show-errors
  fi
}

build_pages
sync_site
upload_pages
cleanup_stale_pages
echo "✓ deployed to s3://$BUCKET"
