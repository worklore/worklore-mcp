#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# Sync static assets with long cache lifetime (e.g., 1 year)
aws s3 sync src/assets/ "s3://$BUCKET/assets/" \
  --cache-control "public, max-age=31536000, immutable" \
  --profile "$PROFILE"

# Sync remaining files (HTML, JS, CSS) with short cache lifetime / revalidation, and handle deletions
aws s3 sync src/ "s3://$BUCKET/" \
  --exclude "assets/*" \
  --cache-control "public, max-age=0, must-revalidate" \
  --delete \
  --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
