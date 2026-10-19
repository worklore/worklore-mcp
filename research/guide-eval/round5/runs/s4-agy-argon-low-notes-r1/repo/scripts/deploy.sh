#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# Sync long-lived static assets with a long Cache-Control TTL
aws s3 sync src/assets/ "s3://$BUCKET/assets/" \
  --cache-control "public, max-age=86400" \
  --delete --profile "$PROFILE"

# Sync HTML, JS, and CSS at the root with a short Cache-Control TTL
aws s3 sync src/ "s3://$BUCKET/" \
  --exclude "assets/*" \
  --cache-control "public, max-age=300" \
  --delete --profile "$PROFILE"

# Explicitly ensure Content-Type and Cache-Control headers travel together on all objects
# (avoids the S3 --metadata-directive REPLACE binary/octet-stream trap and covers already-uploaded files)
for pair in "html:text/html:300" "js:application/javascript:300" \
            "css:text/css:300" "png:image/png:86400" "svg:image/svg+xml:86400"; do
  ext="${pair%%:*}"; rest="${pair#*:}"; ct="${rest%%:*}"; ttl="${rest#*:}"
  aws s3 cp "s3://$BUCKET/" "s3://$BUCKET/" --recursive \
    --exclude "*" --include "*.${ext}" \
    --content-type "$ct" --cache-control "public, max-age=${ttl}" \
    --metadata-directive REPLACE --only-show-errors --profile "$PROFILE"
done

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
