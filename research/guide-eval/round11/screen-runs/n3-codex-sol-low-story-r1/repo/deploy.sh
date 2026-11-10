#!/usr/bin/env bash
# Deploy the site to S3. CI runs this on every push to main with BUCKET set.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
: "${BUCKET:?set BUCKET to the site bucket}"
export AWS_PROFILE="${AWS_PROFILE:-fieldnotes-deploy}"

build_pages() {
  echo "→ building note and author pages"
  rm -rf "$ROOT/.build/pages"
  python3 "$ROOT/build_pages.py" "$ROOT/content/stories.json" "$ROOT/.build/pages"
}

sync_site() {
  echo "→ syncing site/ to s3://$BUCKET"
  aws s3 sync "$ROOT/site/" "s3://$BUCKET/" --delete \
    --exclude 's/*' --exclude 'a/*' --only-show-errors
}

remove_stale_pages() {
  echo "→ removing stale note and author pages"
  python3 - "$ROOT/.build/pages" "$BUCKET" <<'PY'
import json
import pathlib
import subprocess
import sys

pages, bucket = pathlib.Path(sys.argv[1]), sys.argv[2]
for prefix in ("s/", "a/"):
    folder = pages / prefix
    current = {p.relative_to(pages).as_posix() for p in folder.rglob("*")
               if p.is_file()} if folder.exists() else set()
    token = None
    stale = []
    while True:
        command = ["aws", "s3api", "list-objects-v2", "--bucket", bucket,
                   "--prefix", prefix, "--output", "json", "--no-paginate"]
        if token:
            command += ["--continuation-token", token]
        result = json.loads(subprocess.check_output(command))
        for obj in result.get("Contents", []):
            key = obj["Key"]
            if key not in current:
                stale.append(key)
        token = result.get("NextContinuationToken")
        if not token:
            break
    for key in stale:
        subprocess.run(["aws", "s3api", "delete-object", "--bucket", bucket,
                        "--key", key], check=True, stdout=subprocess.DEVNULL)
PY
}

upload_pages() {
  # Page keys are extensionless (s/<slug>, a/<handle>), so S3 can't guess their
  # type: upload each one with text/html.
  echo "→ uploading pages"
  ( cd "$ROOT/.build/pages" && find . -type f | sed 's|^\./||' | sort | while read -r key; do
      aws s3 cp "$key" "s3://$BUCKET/$key" --content-type "text/html; charset=utf-8" \
        --cache-control "max-age=300" --only-show-errors
    done )
}

build_pages
sync_site
upload_pages
remove_stale_pages
echo "✓ deployed to s3://$BUCKET"
