#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
#
# Cache policy: HTML, JS and CSS are short-lived so returning visitors pick up
# a new booking.js within minutes. Anything under assets/ is cached a day.
# Headers are set by re-uploading each file from disk with an explicit
# content type. Never copy objects in S3 with --metadata-directive REPLACE
# (it drops Content-Type, and browsers then refuse to run the files).
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

SHORT_CACHE="public, max-age=300"
LONG_CACHE="public, max-age=86400"

content_type_for() {
  case "$1" in
    *.html) echo "text/html; charset=utf-8" ;;
    *.js)   echo "application/javascript; charset=utf-8" ;;
    *.css)  echo "text/css; charset=utf-8" ;;
    *.png)  echo "image/png" ;;
    *.svg)  echo "image/svg+xml" ;;
    *) return 1 ;;
  esac
}

# Check every file has a known type before touching the bucket.
while IFS= read -r -d '' file; do
  content_type_for "$file" > /dev/null || {
    echo "no content type for $file; add it to content_type_for" >&2
    exit 1
  }
done < <(find src -type f -print0)

aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

while IFS= read -r -d '' file; do
  key="${file#src/}"
  case "$key" in
    assets/*) cache="$LONG_CACHE" ;;
    *)        cache="$SHORT_CACHE" ;;
  esac
  aws s3 cp "$file" "s3://$BUCKET/$key" \
    --content-type "$(content_type_for "$file")" \
    --cache-control "$cache" \
    --profile "$PROFILE" --only-show-errors
done < <(find src -type f -print0)

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
