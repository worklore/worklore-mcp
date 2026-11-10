#!/usr/bin/env bash
# Deploy the site to S3. CI runs this on every push to main with BUCKET set.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
: "${BUCKET:?set BUCKET to the site bucket}"
export AWS_PROFILE="${AWS_PROFILE:-fieldnotes-deploy}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

build_pages() {
  echo "→ building note and author pages"
  rm -rf "$ROOT/.build/pages"
  python3 "$ROOT/build_pages.py" "$ROOT/content/stories.json" "$ROOT/.build/pages"
}

sync_site() {
  # No --delete: the bucket also holds page keys, which must not be touched here.
  # Files removed from site/ are removed by prune_stale.
  echo "→ syncing site/ to s3://$BUCKET"
  aws s3 sync "$ROOT/site/" "s3://$BUCKET/" --only-show-errors
}

upload_pages() {
  # Page keys are extensionless (s/<slug>, a/<handle>), so S3 can't guess their
  # type: upload each one with text/html. Each cp overwrites the live key in
  # place, so a page is never missing during the deploy.
  echo "→ uploading pages"
  ( cd "$ROOT/.build/pages" && find . -type f | sed 's|^\./||' | sort | while read -r key; do
      aws s3 cp "$key" "s3://$BUCKET/$key" --content-type "text/html; charset=utf-8" \
        --cache-control "max-age=300" --only-show-errors
    done )
}

prune_stale() {
  # Delete every key in the bucket that this build did not produce: not a site/
  # file and not a page. Runs after the uploads, so only stale keys are removed.
  echo "→ removing keys this build no longer produces"
  {
    ( cd "$ROOT/site" && find . -type f | sed 's|^\./||' )
    ( cd "$ROOT/.build/pages" && find . -type f | sed 's|^\./||' )
  } | LC_ALL=C sort > "$TMP/expected"
  # Refuse to prune if the build produced nothing: that would empty the bucket.
  [ -s "$TMP/expected" ] || { echo "✗ build produced no files; not pruning" >&2; exit 1; }

  aws s3api list-objects-v2 --bucket "$BUCKET" --query 'Contents[].Key' --output text > "$TMP/listing"
  # An empty bucket lists as "None".
  tr '\t' '\n' < "$TMP/listing" | sed '/^None$/d; /^$/d' | LC_ALL=C sort > "$TMP/bucket"
  LC_ALL=C comm -23 "$TMP/bucket" "$TMP/expected" > "$TMP/stale"

  while IFS= read -r key; do
    echo "  removing $key"
    aws s3 rm "s3://$BUCKET/$key" --only-show-errors </dev/null
  done < "$TMP/stale"
}

build_pages
sync_site
upload_pages
prune_stale
echo "✓ deployed to s3://$BUCKET"
