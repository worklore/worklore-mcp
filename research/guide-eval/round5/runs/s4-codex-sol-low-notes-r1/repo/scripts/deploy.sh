#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

# Upload with explicit content types so cache metadata cannot make pages or
# scripts download as binary files. Re-upload even unchanged files: sync does
# not update metadata on objects whose content has not changed.
for spec in \
  "html:text/html:300" \
  "js:application/javascript:300" \
  "css:text/css:300" \
  "png:image/png:86400" \
  "svg:image/svg+xml:86400"; do
  ext="${spec%%:*}"
  rest="${spec#*:}"
  content_type="${rest%%:*}"
  max_age="${rest#*:}"
  aws s3 cp src/ "s3://$BUCKET/" --recursive \
    --exclude "*" --include "*.$ext" \
    --content-type "$content_type" \
    --cache-control "public, max-age=$max_age" \
    --only-show-errors --profile "$PROFILE"
done

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
