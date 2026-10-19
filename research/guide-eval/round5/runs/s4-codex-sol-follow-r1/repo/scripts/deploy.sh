#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

content_type_for() {
  case "$1" in
    *.html) content_type="text/html" ;;
    *.js)   content_type="application/javascript" ;;
    *.css)  content_type="text/css" ;;
    *.png)  content_type="image/png" ;;
    *.svg)  content_type="image/svg+xml" ;;
    *) echo "Unknown content type for $1" >&2; return 1 ;;
  esac
}

# Check every file before making any changes to the bucket.
while IFS= read -r -d '' file; do
  content_type_for "${file#src/}"
done < <(find src -type f -print0)

while IFS= read -r -d '' file; do
  key="${file#src/}"
  content_type_for "$key"
  case "$key" in
    assets/*) max_age=86400 ;;
    *)        max_age=300 ;;
  esac
  aws s3 cp "$file" "s3://$BUCKET/$key" \
    --content-type "$content_type" \
    --cache-control "public, max-age=$max_age" \
    --only-show-errors --profile "$PROFILE"
done < <(find src -type f -print0)

# The uploads above also refresh metadata on unchanged files.
aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
