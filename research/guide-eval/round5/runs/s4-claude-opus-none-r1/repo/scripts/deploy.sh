#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# HTML, JS, CSS: browsers may reuse for a minute, then must revalidate.
SHORT_CACHE="public, max-age=60, must-revalidate"
# assets/: cached for a year. File names are not fingerprinted, so to change
# an asset, upload it under a new name and update the references.
LONG_CACHE="public, max-age=31536000"

# cp (not sync) so every object is re-uploaded with its header, including
# files that haven't changed since they were first uploaded without one.
aws s3 cp src/assets/ "s3://$BUCKET/assets/" --recursive \
  --cache-control "$LONG_CACHE" --profile "$PROFILE"
aws s3 cp src/ "s3://$BUCKET/" --recursive --exclude "assets/*" \
  --cache-control "$SHORT_CACHE" --profile "$PROFILE"

# Remove objects that no longer exist in src/. Each pass carries the matching
# header in case it uploads anything.
aws s3 sync src/assets/ "s3://$BUCKET/assets/" --delete \
  --cache-control "$LONG_CACHE" --profile "$PROFILE"
aws s3 sync src/ "s3://$BUCKET/" --delete --exclude "assets/*" \
  --cache-control "$SHORT_CACHE" --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
