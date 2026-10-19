#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
#
# Every object is uploaded with an explicit Content-Type AND Cache-Control,
# set together per file type, so one can never be changed without the other:
#   - HTML / JS / CSS (top level): short cache, so a new booking.js reaches
#     returning visitors within minutes of a deploy.
#   - assets/: long cache. These files are not fingerprinted, so to change
#     one, give it a new filename rather than overwriting it.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

SHORT="public, max-age=300"
LONG="public, max-age=2592000"   # 30 days

# ext:content-type:cache-control-variable:path-prefix
RULES=(
  "html:text/html; charset=utf-8:SHORT:"
  "js:application/javascript; charset=utf-8:SHORT:"
  "css:text/css; charset=utf-8:SHORT:"
  "png:image/png:LONG:assets/"
  "svg:image/svg+xml:LONG:assets/"
)

# Refuse to deploy files that no rule covers: they would go up with no
# Cache-Control (or a guessed type), which is the bug this script fixes.
known=()
for rule in "${RULES[@]}"; do
  IFS=: read -r ext _ _ prefix <<<"$rule"
  known+=(-not -path "src/${prefix}*.${ext}")
done
unknown=$(find src -type f "${known[@]}")
if [[ -n "$unknown" ]]; then
  echo "deploy: no content-type/cache rule for:" >&2
  echo "$unknown" >&2
  exit 1
fi

# cp (not sync) so every object is re-uploaded with its headers each deploy,
# including files whose bytes did not change. The site is small.
for rule in "${RULES[@]}"; do
  IFS=: read -r ext ct policy prefix <<<"$rule"
  aws s3 cp src/ "s3://$BUCKET/" --recursive \
    --exclude "*" --include "${prefix}*.${ext}" \
    --content-type "$ct" --cache-control "${!policy}" \
    --only-show-errors --profile "$PROFILE"
done

# Remove objects that no longer exist in src/. --size-only: everything was
# just uploaded above, so this pass should only delete, never re-upload
# (a re-upload here would drop the headers).
aws s3 sync src/ "s3://$BUCKET/" --delete --size-only \
  --only-show-errors --profile "$PROFILE"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
echo "check: curl -sI https://<site>/booking.js | grep -iE 'content-type|cache-control'"
