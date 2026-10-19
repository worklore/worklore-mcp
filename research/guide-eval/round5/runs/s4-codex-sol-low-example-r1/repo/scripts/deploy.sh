#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

# Upload every file, including unchanged ones, so existing objects get the headers.
# Explicit content types avoid losing the browser-readable type during metadata updates.
while IFS= read -r -d '' file; do
  key="${file#src/}"
  case "$key" in
    *.html) content_type="text/html" ;;
    *.js) content_type="application/javascript" ;;
    *.css) content_type="text/css" ;;
    assets/*.png) content_type="image/png" ;;
    assets/*.svg) content_type="image/svg+xml" ;;
    *) echo "Unknown content type: $key" >&2; exit 1 ;;
  esac

  if [[ "$key" == assets/* ]]; then
    cache_control="public, max-age=31536000"
  else
    cache_control="public, max-age=300"
  fi

  aws s3 cp "$file" "s3://$BUCKET/$key" \
    --content-type "$content_type" --cache-control "$cache_control" \
    --profile "$PROFILE" --only-show-errors
done < <(find src -type f -print0)

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
