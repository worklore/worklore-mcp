#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# Sync removes files deleted from src/. Its cache policy also covers new file
# types until the copies below apply the policy for their path.
aws s3 sync src/ "s3://$BUCKET/" --delete \
  --cache-control "public, max-age=300" --profile "$PROFILE"

# Sync skips unchanged files, including objects uploaded before cache headers
# were added. Copy every local file so each deploy refreshes its S3 metadata.
# These are local-to-S3 copies: no metadata replacement or MIME loss.
while IFS= read -r -d '' file; do
  path="${file#src/}"
  cache_control="public, max-age=300"
  case "$path" in
    assets/*) cache_control="public, max-age=86400" ;;
  esac

  content_type=()
  case "$path" in
    *.html) content_type=(--content-type "text/html") ;;
    *.js)   content_type=(--content-type "application/javascript") ;;
    *.css)  content_type=(--content-type "text/css") ;;
    *.png)  content_type=(--content-type "image/png") ;;
    *.svg)  content_type=(--content-type "image/svg+xml") ;;
  esac

  aws s3 cp "$file" "s3://$BUCKET/$path" \
    --cache-control "$cache_control" "${content_type[@]}" \
    --profile "$PROFILE" --only-show-errors
done < <(find src -type f -print0)

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
