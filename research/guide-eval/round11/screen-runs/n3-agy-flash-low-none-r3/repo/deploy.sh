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

assemble_site() {
  echo "→ assembling complete site in .build/site"
  rm -rf "$ROOT/.build/site"
  mkdir -p "$ROOT/.build/site"
  cp -R "$ROOT/site/." "$ROOT/.build/site/"
  cp -R "$ROOT/.build/pages/." "$ROOT/.build/site/"
}

sync_site() {
  # Sync static site files and prune removed files from the bucket
  echo "→ syncing site to s3://$BUCKET"
  aws s3 sync "$ROOT/.build/site/" "s3://$BUCKET/" --delete --only-show-errors
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
assemble_site
sync_site
upload_pages
echo "✓ deployed to s3://$BUCKET"
