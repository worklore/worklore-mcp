#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# Short cache for pages and code, so a deploy reaches returning visitors
# within minutes. Long cache for assets/, which are not fingerprinted, so
# a changed logo still arrives within a day.
SHORT_CACHE="public, max-age=300"
LONG_CACHE="public, max-age=86400"

# Refuse to deploy a file type this script has no content type for.
unhandled=$(find src -type f ! \( -name '*.html' -o -name '*.js' -o -name '*.css' \
  -o -name '*.png' -o -name '*.svg' \))
if [ -n "$unhandled" ]; then
  echo "no content type set for these files:" >&2
  echo "$unhandled" >&2
  exit 1
fi

# Remove objects that no longer exist locally.
aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

# sync skips files whose size and mtime are unchanged, so it would never fix
# objects uploaded without headers. Re-upload each type from src/ with its
# content type and cache policy stated explicitly.
upload() {  # upload <extension> <content-type> <cache-control>
  aws s3 cp src/ "s3://$BUCKET/" --recursive \
    --exclude "*" --include "*.$1" \
    --content-type "$2" --cache-control "$3" \
    --profile "$PROFILE" --only-show-errors
}
upload html "text/html; charset=utf-8" "$SHORT_CACHE"
upload js "application/javascript; charset=utf-8" "$SHORT_CACHE"
upload css "text/css; charset=utf-8" "$SHORT_CACHE"
upload png "image/png" "$LONG_CACHE"
upload svg "image/svg+xml" "$LONG_CACHE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
