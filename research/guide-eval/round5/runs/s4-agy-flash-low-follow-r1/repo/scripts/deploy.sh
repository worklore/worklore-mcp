#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

# Set Cache-Control headers per file extension, ensuring Content-Type is preserved/specified explicitly.
# Short TTL (max-age=300) for HTML, JS, CSS in root / general code; long TTL (max-age=86400 or 31536000) for assets/
for pair in "html:text/html:300" "js:application/javascript:300" "css:text/css:300"; do
  ext="${pair%%:*}"; rest="${pair#*:}"; ct="${rest%%:*}"; ttl="${rest#*:}"
  aws s3 cp "s3://$BUCKET/" "s3://$BUCKET/" --recursive \
    --exclude "*" --include "*.${ext}" \
    --content-type "$ct" --cache-control "public, max-age=${ttl}" \
    --metadata-directive REPLACE --only-show-errors --profile "$PROFILE"
done

# Long TTL for assets/
for pair in "png:image/png:31536000" "svg:image/svg+xml:31536000"; do
  ext="${pair%%:*}"; rest="${pair#*:}"; ct="${rest%%:*}"; ttl="${rest#*:}"
  aws s3 cp "s3://$BUCKET/assets/" "s3://$BUCKET/assets/" --recursive \
    --exclude "*" --include "*.${ext}" \
    --content-type "$ct" --cache-control "public, max-age=${ttl}" \
    --metadata-directive REPLACE --only-show-errors --profile "$PROFILE"
done

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
