#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
#
# Cache policy is set on upload, from the local file:
#   - assets/ (logo, icons): long-lived, one year
#   - everything else (html, css, js): short, five minutes
#
# Every file is re-uploaded on each deploy, so none is left with a stale or
# missing Cache-Control header. Content-Type is guessed from the extension by
# the AWS CLI when it reads the local file.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"
SHORT_CACHE="public, max-age=300"
LONG_CACHE="public, max-age=31536000"

aws s3 cp src/ "s3://$BUCKET/" --recursive --exclude "assets/*" \
  --cache-control "$SHORT_CACHE" --profile "$PROFILE"

aws s3 cp src/assets/ "s3://$BUCKET/assets/" --recursive \
  --cache-control "$LONG_CACHE" --profile "$PROFILE"

# Remove objects whose local files were deleted. Files just uploaded above are
# identical, so sync does not re-upload them and their headers stay as set.
aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
