#!/usr/bin/env bash
# Deploy the site to S3. CI runs this on every push to main with BUCKET set.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
: "${BUCKET:?set BUCKET to the site bucket}"
export AWS_PROFILE="${AWS_PROFILE:-fieldnotes-deploy}"

build_site() {
  echo "→ staging site assets and building pages"
  rm -rf "$ROOT/.build/site"
  mkdir -p "$ROOT/.build/site"
  cp -R "$ROOT/site/." "$ROOT/.build/site/"
  python3 "$ROOT/build_pages.py" "$ROOT/content/stories.json" "$ROOT/.build/site"
}

sync_bucket() {
  # Sync everything to the bucket and delete files no longer produced by the build.
  # Extensionless pages (s/<slug>, a/<handle>) need text/html content-type.
  echo "→ syncing to s3://$BUCKET"
  aws s3 sync "$ROOT/.build/site" "s3://$BUCKET" \
    --delete \
    --exclude "s/*" \
    --exclude "a/*" \
    --only-show-errors

  aws s3 sync "$ROOT/.build/site/s" "s3://$BUCKET/s" \
    --delete \
    --content-type "text/html; charset=utf-8" \
    --cache-control "max-age=300" \
    --only-show-errors

  aws s3 sync "$ROOT/.build/site/a" "s3://$BUCKET/a" \
    --delete \
    --content-type "text/html; charset=utf-8" \
    --cache-control "max-age=300" \
    --only-show-errors
}

build_site
sync_bucket
echo "✓ deployed to s3://$BUCKET"
