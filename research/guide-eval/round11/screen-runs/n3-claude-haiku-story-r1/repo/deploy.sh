#!/usr/bin/env bash
# Deploy the site to S3. CI runs this on every push to main with BUCKET set.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
: "${BUCKET:?set BUCKET to the site bucket}"
export AWS_PROFILE="${AWS_PROFILE:-fieldnotes-deploy}"

build_pages() {
  echo "→ building note and author pages"
  rm -rf "$ROOT/.build/pages"
  mkdir -p "$ROOT/.build/pages"  # build_pages.py writes nothing when there are no notes
  python3 "$ROOT/build_pages.py" "$ROOT/content/stories.json" "$ROOT/.build/pages"
}

page_keys() {
  ( cd "$ROOT/.build/pages" && find . -type f | sed 's|^\./||' | sort )
}

sync_site() {
  echo "→ syncing site/ to s3://$BUCKET"
  # --delete removes everything in the bucket that this build no longer produces:
  # removed site/ files and stale or unpublished pages. Pages this build does
  # produce are excluded, so the sync never removes a live page; upload_pages
  # overwrites them in place. (--exclude matches the exact key, no wildcards.)
  local excludes=()
  local key
  while IFS= read -r key; do
    excludes+=(--exclude "$key")
  done < <(page_keys)
  aws s3 sync "$ROOT/site/" "s3://$BUCKET/" --delete \
    ${excludes[@]+"${excludes[@]}"} --only-show-errors
}

upload_pages() {
  # Page keys are extensionless (s/<slug>, a/<handle>), so S3 can't guess their
  # type: upload each one with text/html. Each cp overwrites the old page in
  # place, so the old version stays served until the new one replaces it.
  echo "→ uploading pages"
  ( cd "$ROOT/.build/pages" && page_keys | while read -r key; do
      aws s3 cp "$key" "s3://$BUCKET/$key" --content-type "text/html; charset=utf-8" \
        --cache-control "max-age=300" --only-show-errors
    done )
}

build_pages
sync_site
upload_pages
echo "✓ deployed to s3://$BUCKET"
