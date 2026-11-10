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

# S3 keys of the generated pages.
page_keys() { ( cd "$ROOT/.build/pages" && find . -type f | sed 's|^\./||' ); }

sync_site() {
  # The pages are not in site/, so a plain --delete would remove every one of them until upload_pages puts it back.
  # Keep them out of the delete; upload_pages overwrites them in place and prune_pages removes stale ones.
  echo "→ syncing site/ to s3://$BUCKET"
  aws s3 sync "$ROOT/site/" "s3://$BUCKET/" --delete --exclude 's/*' --exclude 'a/*' --only-show-errors
}

prune_pages() {
  echo "→ pruning stale pages"
  local keep; keep="$(page_keys)"
  aws s3api list-objects-v2 --bucket "$BUCKET" --query 'Contents[].Key' --output text \
    | tr '\t' '\n' | grep -E '^(s|a)/[^.]+$' | while read -r key; do
      grep -qxF "$key" <<<"$keep" || { echo "  - $key"; aws s3 rm "s3://$BUCKET/$key" --only-show-errors; }
    done
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
prune_pages
echo "✓ deployed to s3://$BUCKET"
