#!/usr/bin/env bash
# Upload src/ to the bucket and invalidate CloudFront.
#
# Every object is uploaded with an explicit Content-Type AND Cache-Control,
# set together from the table below. Never set one without the other: an
# upload or copy that passes --cache-control but no --content-type (e.g.
# `s3 cp --metadata-directive REPLACE`) leaves objects as binary/octet-stream
# and the site stops rendering while every request still returns 200.
set -euo pipefail
cd "$(dirname "$0")/.."

BUCKET="ruta-ceramica-site-7f3a"
DISTRIBUTION_ID="E2QX9ZK1DEMO01"
PROFILE="studio"

SHORT="public, max-age=300"    # HTML, JS, CSS: returning visitors re-check within 5 min
LONG="public, max-age=86400"   # assets/: 1 day (filenames are not fingerprinted)

# scope:extension:content-type   (scope "code" = outside assets/, "assets" = under assets/)
RULES=(
  "code:html:text/html; charset=utf-8"
  "code:js:application/javascript; charset=utf-8"
  "code:css:text/css; charset=utf-8"
  "assets:png:image/png"
  "assets:svg:image/svg+xml"
)

# Refuse to deploy any file the table does not cover, so nothing is ever
# uploaded with a missing or guessed type/cache policy.
uncovered=0
while IFS= read -r -d '' f; do
  rel="${f#src/}"; ext="${rel##*.}"
  case "$rel" in assets/*) scope=assets ;; *) scope=code ;; esac
  ok=0
  for rule in "${RULES[@]}"; do
    [[ "$rule" == "$scope:$ext:"* ]] && ok=1 && break
  done
  if [[ $ok -eq 0 ]]; then
    echo "deploy.sh: no content-type/cache rule for '$rel' ($scope, .$ext) — add one to RULES" >&2
    uncovered=1
  fi
done < <(find src -type f ! -name '.*' -print0)
[[ $uncovered -eq 0 ]] || exit 1

for rule in "${RULES[@]}"; do
  scope="${rule%%:*}"; rest="${rule#*:}"; ext="${rest%%:*}"; ct="${rest#*:}"
  if [[ "$scope" == assets ]]; then
    filters=(--exclude "*" --include "assets/*.${ext}")
    cc="$LONG"
  else
    filters=(--exclude "*" --include "*.${ext}" --exclude "assets/*")
    cc="$SHORT"
  fi
  aws s3 cp src/ "s3://$BUCKET/" --recursive "${filters[@]}" \
    --content-type "$ct" --cache-control "$cc" \
    --only-show-errors --profile "$PROFILE"
done

# Remove objects that no longer exist in src/. Everything was just uploaded,
# so with --size-only this only deletes; it never re-uploads (which would
# drop the headers set above).
aws s3 sync src/ "s3://$BUCKET/" --delete --size-only \
  --only-show-errors --profile "$PROFILE"

# Read the headers back. A successful upload is not proof the site works.
check() {
  local key="$1" want_ct="$2" want_cc="$3" got
  got="$(aws s3api head-object --bucket "$BUCKET" --key "$key" --profile "$PROFILE" \
    --query '[ContentType, CacheControl]' --output text)"
  if [[ "$got" != "$want_ct"$'\t'"$want_cc" ]]; then
    echo "deploy.sh: $key has wrong headers: '$got' (want '$want_ct' / '$want_cc')" >&2
    exit 1
  fi
}
check index.html      "text/html; charset=utf-8"              "$SHORT"
check booking.js      "application/javascript; charset=utf-8" "$SHORT"
check styles.css      "text/css; charset=utf-8"               "$SHORT"
check assets/logo.png "image/png"                             "$LONG"

# The edge has the old (header-less) copies cached too.
aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" --profile "$PROFILE" > /dev/null

echo "deployed"
