#!/usr/bin/env bash
# Deploy the site to S3. CI runs this on every push to main with BUCKET set.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
: "${BUCKET:?set BUCKET to the site bucket}"
export AWS_PROFILE="${AWS_PROFILE:-fieldnotes-deploy}"

build_pages() {
  echo "→ building note and author pages"
  rm -rf "$ROOT/.build/pages"
  mkdir -p "$ROOT/.build/pages"
  python3 "$ROOT/build_pages.py" "$ROOT/content/stories.json" "$ROOT/.build/pages"
}

sync_site() {
  # Sync the complete desired bucket contents so --delete also removes old
  # note and author pages, as well as files removed from site/.
  echo "→ syncing site and pages to s3://$BUCKET"
  rm -rf "$ROOT/.build/deploy"
  mkdir -p "$ROOT/.build/deploy"
  cp -R "$ROOT/site/." "$ROOT/.build/deploy/"
  cp -R "$ROOT/.build/pages/." "$ROOT/.build/deploy/"
  aws s3 sync "$ROOT/.build/deploy/" "s3://$BUCKET/" --delete --only-show-errors
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

build_pages
sync_site
upload_pages
echo "✓ deployed to s3://$BUCKET"
