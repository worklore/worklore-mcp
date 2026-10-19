#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

aws s3 sync src/assets/ "s3://$BUCKET/assets/" --cache-control "max-age=31536000, public" --profile "$PROFILE"
aws s3 sync src/ "s3://$BUCKET/" --delete --exclude "assets/*" --cache-control "max-age=0, public, must-revalidate" --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
