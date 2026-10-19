#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# Sync all files except HTML, JS, and assets
aws s3 sync src/ "s3://$BUCKET/" --delete --exclude "*.html" --exclude "*.js" --exclude "assets/*" --profile "$PROFILE"

# Upload HTML and JS with short caching (e.g., 60 seconds)
aws s3 cp src/ "s3://$BUCKET/" --recursive --exclude "*" --include "*.html" --include "*.js" --cache-control "max-age=60, public" --profile "$PROFILE"

# Upload assets with long caching (e.g., 1 year)
aws s3 cp src/assets/ "s3://$BUCKET/assets/" --recursive --cache-control "max-age=31536000, public" --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
