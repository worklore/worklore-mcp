#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# Sync site files with appropriate Cache-Control and Content-Type headers:
# - Short cache for HTML and JS (and CSS) so updates propagate quickly
# - Long cache for assets/ (images, icons, etc.)
# Note: S3 sync uploads new/changed files and deletes removed files.
aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

# Apply short cache-control to root code files (HTML, JS, CSS)
for pair in "html:text/html:300" "js:application/javascript:300" "css:text/css:300"; do
  ext="${pair%%:*}"; rest="${pair#*:}"; ct="${rest%%:*}"; ttl="${rest#*:}"
  aws s3 cp "s3://$BUCKET/" "s3://$BUCKET/" --recursive \
    --exclude "*" --include "*.${ext}" --exclude "assets/*" \
    --content-type "$ct" --cache-control "public, max-age=${ttl}" \
    --metadata-directive REPLACE --only-show-errors --profile "$PROFILE"
done

# Apply long cache-control to assets/
for pair in "png:image/png:31536000" "svg:image/svg+xml:31536000"; do
  ext="${pair%%:*}"; rest="${pair#*:}"; ct="${rest%%:*}"; ttl="${rest#*:}"
  aws s3 cp "s3://$BUCKET/assets/" "s3://$BUCKET/assets/" --recursive \
    --exclude "*" --include "*.${ext}" \
    --content-type "$ct" --cache-control "public, max-age=${ttl}, immutable" \
    --metadata-directive REPLACE --only-show-errors --profile "$PROFILE"
done

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
