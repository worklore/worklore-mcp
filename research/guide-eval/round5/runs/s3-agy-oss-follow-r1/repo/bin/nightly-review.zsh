#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$SCRIPT_DIR/notify.sh"

if date -v -1d +%F >/dev/null 2>&1; then
  SINCE=$(date -v -1d +%F)
else
  SINCE=$(date -d "yesterday" +%F)
fi

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
