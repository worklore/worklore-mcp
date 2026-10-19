#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# Cache policy and Content-Type are always set together, per extension.
# Never re-apply headers with `--metadata-directive REPLACE` without a
# --content-type: it wipes the type and the site is served as octet-stream.
SHORT="public, max-age=300"          # HTML, CSS, JS: changes show up within 5 min
LONG="public, max-age=2592000"       # assets/ (30 days); rename a file to change it early

# Fail if src/ holds a file type we have no Content-Type for.
unknown=$(find src -type f ! -name '*.html' ! -name '*.js' ! -name '*.css' \
  ! -name '*.png' ! -name '*.svg' || true)
if [ -n "$unknown" ]; then
  echo "No Content-Type mapping for:" >&2; echo "$unknown" >&2; exit 1
fi

# assets/: long cache.
for pair in "png:image/png" "svg:image/svg+xml"; do
  aws s3 sync src/assets/ "s3://$BUCKET/assets/" --delete --exclude "*" \
    --include "*.${pair%%:*}" --content-type "${pair#*:}" \
    --cache-control "$LONG" --profile "$PROFILE"
done

# Everything else: short cache.
for pair in "html:text/html" "js:application/javascript" "css:text/css"; do
  aws s3 sync src/ "s3://$BUCKET/" --delete --exclude "assets/*" --exclude "*" \
    --include "*.${pair%%:*}" --content-type "${pair#*:}" \
    --cache-control "$SHORT" --profile "$PROFILE"
done

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
