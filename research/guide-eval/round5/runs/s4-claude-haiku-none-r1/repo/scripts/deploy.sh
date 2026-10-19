#!/usr/bin/env bash
# Upload src/ to the bucket, set Cache-Control per file type, invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# HTML, JS and CSS change with every release, so browsers revalidate after 5 minutes.
SHORT_CACHE="public, max-age=300, must-revalidate"
# assets/ files are not fingerprinted, so these are cached for a year.
# To change one, rename it (e.g. logo.v2.png) so the URL changes.
LONG_CACHE="public, max-age=31536000"

# 1. Sync adds, updates and deletes objects. It skips files whose size and
#    timestamp are unchanged, so it cannot be relied on to set headers.
aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

# 2. Re-copy everything so each object gets its Cache-Control header.
#    Existing objects from before this change have none, so they need this too.
aws s3 cp src/ "s3://$BUCKET/" --recursive --exclude "assets/*" \
  --cache-control "$SHORT_CACHE" --profile "$PROFILE"

aws s3 cp src/assets/ "s3://$BUCKET/assets/" --recursive \
  --cache-control "$LONG_CACHE" --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
