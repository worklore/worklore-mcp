#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

# Upload every file again so unchanged objects also receive the new headers.
# Keep Content-Type with Cache-Control: replacing metadata without a type can
# make browsers download HTML and reject scripts as binary/octet-stream.
while IFS= read -r -d '' file; do
  key="${file#src/}"
  case "$key" in
    *.html) content_type="text/html"; max_age=300 ;;
    *.js) content_type="application/javascript"; max_age=300 ;;
    *.css) content_type="text/css"; max_age=300 ;;
    assets/*.png) content_type="image/png"; max_age=86400 ;;
    assets/*.svg) content_type="image/svg+xml"; max_age=86400 ;;
    *) echo "No cache policy for $key" >&2; exit 1 ;;
  esac
  aws s3 cp "$file" "s3://$BUCKET/$key" \
    --content-type "$content_type" \
    --cache-control "public, max-age=$max_age" \
    --profile "$PROFILE" --only-show-errors
done < <(find src -type f -print0)

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
