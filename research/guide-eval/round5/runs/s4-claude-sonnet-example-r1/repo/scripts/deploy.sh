#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
# Content-Type and Cache-Control are always set together, per extension, so
# neither can be lost when the other is changed.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

# ext:content-type:cache-control
# HTML and JS (booking.js) are short so a deploy reaches visitors within minutes;
# CSS rides with them. Files under assets/ are long-lived.
CODE_CC="public, max-age=300"
ASSET_CC="public, max-age=31536000"
RULES=(
  "html:text/html; charset=utf-8:$CODE_CC"
  "js:application/javascript; charset=utf-8:$CODE_CC"
  "css:text/css; charset=utf-8:$CODE_CC"
)
ASSET_RULES=(
  "png:image/png:$ASSET_CC"
  "svg:image/svg+xml:$ASSET_CC"
)

# Refuse to upload a file type we have no Content-Type for.
unknown=$(find src -type f ! -name '*.html' ! -name '*.js' ! -name '*.css' \
  ! -path 'src/assets/*' -print; \
  find src/assets -type f ! -name '*.png' ! -name '*.svg' -print)
if [ -n "$unknown" ]; then
  echo "No Content-Type rule for:" >&2; echo "$unknown" >&2; exit 1
fi

# cp (not sync) so unchanged files are re-uploaded too: sync skips them and
# they would keep their old, header-less metadata.
upload() { # src-dir dest-prefix rule...
  local dir="$1" prefix="$2" rule ext rest ct cc; shift 2
  for rule in "$@"; do
    ext="${rule%%:*}"; rest="${rule#*:}"; ct="${rest%%:*}"; cc="${rest#*:}"
    aws s3 cp "$dir" "s3://$BUCKET/$prefix" --recursive \
      --exclude "*" --include "*.${ext}" \
      --content-type "$ct" --cache-control "$cc" \
      --only-show-errors --profile "$PROFILE"
  done
}

upload src ""  "${RULES[@]}"
upload src/assets "assets/" "${ASSET_RULES[@]}"

# Remove files no longer in src/. Everything was just uploaded, so S3 copies are
# newer than the local ones and sync skips them (keeping their headers); it only
# deletes stale objects.
aws s3 sync src/ "s3://$BUCKET/" --delete --only-show-errors --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
echo "verify: curl -sI https://<site>/booking.js | grep -iE 'content-type|cache-control'"
