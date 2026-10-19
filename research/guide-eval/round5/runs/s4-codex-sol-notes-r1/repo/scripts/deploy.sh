#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# Sync removes deleted files. The copies below also refresh metadata on files
# whose contents have not changed, since sync skips those objects.
aws s3 sync src/ "s3://$BUCKET/" --delete \
  --cache-control "public, max-age=300" --profile "$PROFILE"

for file_type in \
  "html:text/html" \
  "js:application/javascript" \
  "css:text/css"; do
  extension="${file_type%%:*}"
  content_type="${file_type#*:}"
  aws s3 cp src/ "s3://$BUCKET/" --recursive \
    --exclude "*" --include "*.${extension}" --exclude "assets/*" \
    --content-type "$content_type" \
    --cache-control "public, max-age=300" \
    --only-show-errors --profile "$PROFILE"
done

# Copy from local files so the CLI detects each asset's MIME type.
aws s3 cp src/assets/ "s3://$BUCKET/assets/" --recursive \
  --cache-control "public, max-age=86400" \
  --only-show-errors --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
