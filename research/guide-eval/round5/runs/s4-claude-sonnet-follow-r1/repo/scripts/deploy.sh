#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
#
# Content-Type and Cache-Control are always set together, per extension, on
# upload. Never run `aws s3 cp --metadata-directive REPLACE` without a
# --content-type: it wipes the type and every object becomes binary/octet-stream.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

SHORT="public, max-age=300"
LONG="public, max-age=86400"

# 1. Mirror src/ (this is the step that removes stale objects). Anything it
#    uploads here gets its headers rewritten in step 2.
aws s3 sync src/ "s3://$BUCKET/" --delete --only-show-errors --profile "$PROFILE"

# 2. Re-upload per extension with type and cache policy together. cp (not sync)
#    so headers are applied even to files whose content did not change.
#    Pages and code: short TTL, so a new booking.js reaches browsers in minutes.
#    Files under assets/: long TTL.
#    Format: "include-pattern|content-type|cache-control"
RULES=(
  "*.html|text/html; charset=utf-8|$SHORT"
  "*.js|application/javascript; charset=utf-8|$SHORT"
  "*.css|text/css; charset=utf-8|$SHORT"
  "assets/*.png|image/png|$LONG"
  "assets/*.svg|image/svg+xml|$LONG"
)
for rule in "${RULES[@]}"; do
  IFS='|' read -r pattern ctype cache <<< "$rule"
  aws s3 cp src/ "s3://$BUCKET/" --recursive \
    --exclude "*" --include "$pattern" \
    --content-type "$ctype" --cache-control "$cache" \
    --only-show-errors --profile "$PROFILE"
done

# 3. Old headers are cached at the edge too.
aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
echo "verify content-type, not just 200:"
echo "  curl -sI https://<site>/ | grep -i -E 'content-type|cache-control'"
echo "  curl -sI https://<site>/booking.js | grep -i -E 'content-type|cache-control'"
