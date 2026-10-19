#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

# Apply proper Cache-Control and Content-Type per file type
pairs=("html:text/html:300" "js:application/javascript:300" "css:text/css:300" "png:image/png:86400" "svg:image/svg+xml:86400")
for pair in "${pairs[@]}"; do
  ext="${pair%%:*}"
  rest="${pair#*:}"
  ct="${rest%%:*}"
  ttl="${rest#*:}"
  aws s3 cp "s3://$BUCKET/" "s3://$BUCKET/" --recursive \
    --exclude "*" --include "*.$ext" \
    --content-type "$ct" --cache-control "public, max-age=$ttl" \
    --metadata-directive REPLACE --profile "$PROFILE" --only-show-errors
done

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
