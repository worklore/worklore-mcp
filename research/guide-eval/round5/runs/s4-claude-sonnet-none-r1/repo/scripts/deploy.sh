#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# Short cache for everything outside assets/ (HTML, JS, CSS: unhashed names,
# so browsers must revalidate soon). Excluded paths are also left alone by --delete.
aws s3 sync src/ "s3://$BUCKET/" --delete --exclude "assets/*" \
  --cache-control "public, max-age=300, must-revalidate" --profile "$PROFILE"

# Long cache for assets/ (logo, images).
aws s3 sync src/assets/ "s3://$BUCKET/assets/" --delete \
  --cache-control "public, max-age=31536000" --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
