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
  aws s3 sync "$ROOT/site/" "s3://$BUCKET/" --only-show-errors
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

prune_bucket() {
  # Anything in the bucket that this build did not produce is stale: the page of
  # a deleted or private note, an author page with no public notes left, or a
  # file removed from site/. Delete those. Runs after the uploads, so a failed
  # upload stops the script before anything is removed.
  echo "→ removing objects the build no longer produces"
  export LC_ALL=C  # comm needs both lists sorted the same way
  local expected="$ROOT/.build/expected-keys" live="$ROOT/.build/live-keys" stale
  { ( cd "$ROOT/site" && find . -type f ); ( cd "$ROOT/.build/pages" && find . -type f ); } \
    | sed 's|^\./||' | sort -u > "$expected"
  # list-objects-v2 returns the literal "None" for an empty bucket; drop it.
  aws s3api list-objects-v2 --bucket "$BUCKET" --output text --query 'Contents[].Key' \
    | tr '\t' '\n' | { grep -v -e '^None$' -e '^$' || true; } | sort -u > "$live"
  stale="$(comm -13 "$expected" "$live")"
  if [ -z "$stale" ]; then
    echo "  nothing stale"
    return
  fi
  while IFS= read -r key; do
    echo "  deleting $key"
    aws s3 rm "s3://$BUCKET/$key" --only-show-errors
  done <<< "$stale"
}

build_pages
sync_site
upload_pages
prune_bucket
echo "✓ deployed to s3://$BUCKET"
