#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

# Re-upload every file in each cache class so existing objects get the new
# metadata too (s3 sync skips unchanged files).
aws s3 cp src/ "s3://$BUCKET/" --recursive --exclude "assets/*" \
  --cache-control "public, max-age=300, must-revalidate" --profile "$PROFILE"
aws s3 cp src/assets/ "s3://$BUCKET/assets/" --recursive \
  --cache-control "public, max-age=31536000" --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
