#!/usr/bin/env bash
# Deploy the site to S3. CI runs this on every push to main with BUCKET set.
#
# Order matters. Live pages must never be missing from the bucket mid-deploy:
#   1. build the pages into .build/pages
#   2. sync site/ with --delete, excluding the page prefixes, so files removed
#      from site/ are deleted but pages are never touched by the sync
#   3. overwrite each page in place (same key, so the old copy serves until replaced)
#   4. delete page keys under those prefixes that this build did not produce
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

# Every page key the build produced, relative to the bucket root (s/<slug>, a/<handle>).
built_keys() {
  ( cd "$ROOT/.build/pages" && find . -type f | sed 's|^\./||' | LC_ALL=C sort )
}

# Top-level folders the build writes pages into (s, a). Each one is owned by the page step.
page_prefixes() {
  ( cd "$ROOT/.build/pages" && find . -mindepth 1 -maxdepth 1 -type d | sed 's|^\./||' | LC_ALL=C sort )
}

# Keys currently in the bucket under one prefix, one per line (paginated by the CLI).
list_keys() {
  aws s3api list-objects-v2 --bucket "$BUCKET" --prefix "$1" \
    --query 'Contents[].Key' --output json \
    | python3 -c 'import json, sys
for key in json.load(sys.stdin) or []:
    print(key)'
}

sync_site() {
  # --exclude keeps the sync's --delete away from the page prefixes. Without it,
  # every page would be deleted on each deploy and re-uploaded one by one.
  local excludes=()
  local prefix
  while read -r prefix; do
    excludes+=(--exclude "$prefix/*")
  done < <(page_prefixes)
  echo "→ syncing site/ to s3://$BUCKET"
  aws s3 sync "$ROOT/site/" "s3://$BUCKET/" --delete \
    ${excludes[@]+"${excludes[@]}"} --only-show-errors
}

upload_pages() {
  # Page keys are extensionless (s/<slug>, a/<handle>), so S3 can't guess their
  # type: upload each one with text/html. Same key as before, so this overwrites in place.
  echo "→ uploading pages"
  ( cd "$ROOT/.build/pages" && built_keys | while read -r key; do
      aws s3 cp "$key" "s3://$BUCKET/$key" --content-type "text/html; charset=utf-8" \
        --cache-control "max-age=300" --only-show-errors
    done )
}

remove_stale_pages() {
  echo "→ removing pages the build no longer produces"
  local built live stale key
  built="$(mktemp)"
  live="$(mktemp)"
  stale="$(mktemp)"
  trap 'rm -f "$built" "$live" "$stale"' RETURN

  built_keys > "$built"
  while read -r prefix; do
    list_keys "$prefix/"
  done < <(page_prefixes) | LC_ALL=C sort > "$live"

  LC_ALL=C comm -23 "$live" "$built" > "$stale"
  while read -r key; do
    [ -n "$key" ] || continue
    echo "  removing s3://$BUCKET/$key"
    aws s3api delete-object --bucket "$BUCKET" --key "$key" > /dev/null
  done < "$stale"
}

build_pages
sync_site
upload_pages
remove_stale_pages
echo "✓ deployed to s3://$BUCKET"
