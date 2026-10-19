#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# HTML, JS and CSS keep their names across deploys, so browsers must recheck
# them soon. assets/ (images) rarely change and can be cached for a long time.
SHORT_CACHE="public, max-age=300"
LONG_CACHE="public, max-age=2592000"

# Upload with `cp` (not `sync`) so every object gets its header on every
# deploy, even files whose content did not change. These are uploads from
# local files, so the CLI still sets Content-Type from the extension; never
# switch this to an in-bucket copy with --metadata-directive REPLACE, which
# wipes Content-Type (see notes/a-cache-header-tweak-...).
# Order: assets first, then code, HTML last, so new pages never reference
# files that are not up yet.
aws s3 cp src/assets/ "s3://$BUCKET/assets/" --recursive \
  --cache-control "$LONG_CACHE" --only-show-errors --profile "$PROFILE"

aws s3 cp src/ "s3://$BUCKET/" --recursive \
  --exclude "assets/*" --exclude "*.html" \
  --cache-control "$SHORT_CACHE" --only-show-errors --profile "$PROFILE"

aws s3 cp src/ "s3://$BUCKET/" --recursive \
  --exclude "*" --include "*.html" \
  --cache-control "$SHORT_CACHE" --only-show-errors --profile "$PROFILE"

# Remove objects that no longer exist locally. Everything is already uploaded,
# so this only deletes.
aws s3 sync src/ "s3://$BUCKET/" --delete --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
