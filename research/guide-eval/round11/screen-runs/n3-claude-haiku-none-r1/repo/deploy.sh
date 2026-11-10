#!/usr/bin/env bash
# Deploy the site to S3. CI runs this on every push to main with BUCKET set.
# The bucket is made to match what the build produces: anything under the
# bucket that the current build no longer generates is deleted.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
: "${BUCKET:?set BUCKET to the site bucket}"
export AWS_PROFILE="${AWS_PROFILE:-fieldnotes-deploy}"

# Prefixes that hold generated pages (s/<slug>, a/<handle>). Only these are
# managed by the page step; everything else in the bucket comes from site/.
PAGE_PREFIXES="s/ a/"

build_pages() {
  echo "→ building note and author pages"
  rm -rf "$ROOT/.build/pages"
  mkdir -p "$ROOT/.build/pages"
  python3 "$ROOT/build_pages.py" "$ROOT/content/stories.json" "$ROOT/.build/pages"
}

sync_site() {
  # --delete removes bucket files that are no longer in site/. The page
  # prefixes are excluded so this step never touches generated pages; S3 sync
  # applies the filters to the destination side too, so they are not deleted here.
  echo "→ syncing site/ to s3://$BUCKET (removing files no longer in site/)"
  aws s3 sync "$ROOT/site/" "s3://$BUCKET/" --delete \
    --exclude "s/*" --exclude "a/*" --only-show-errors
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

prune_pages() {
  # Delete page keys in the bucket that this build did not produce, e.g. notes
  # that were deleted or made private, or authors with no public notes left.
  echo "→ removing pages that are no longer built"
  local built remote stale prefix key
  built="$(cd "$ROOT/.build/pages" && find . -type f | sed 's|^\./||' | LC_ALL=C sort)"
  remote=""
  for prefix in $PAGE_PREFIXES; do
    # A failed listing exits the script here (set -e), so nothing is deleted on a bad read.
    # --output text prints "None" for an empty listing; drop that line.
    raw="$(aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "$prefix" \
      --query 'Contents[].Key' --output text)"
    remote+="$(printf '%s\n' "$raw" | tr '\t' '\n' | grep -v '^None$' || true)"$'\n'
  done
  stale="$(comm -23 <(printf '%s\n' "$remote" | grep -v '^$' | LC_ALL=C sort -u) \
                    <(printf '%s\n' "$built" | grep -v '^$' | LC_ALL=C sort -u))"
  if [ -z "$stale" ]; then
    echo "  nothing to remove"
    return
  fi
  while read -r key; do
    [ -n "$key" ] || continue
    echo "  removing $key"
    aws s3 rm "s3://$BUCKET/$key" --only-show-errors
  done <<< "$stale"
}

build_pages
sync_site
upload_pages
prune_pages
echo "✓ deployed to s3://$BUCKET"
