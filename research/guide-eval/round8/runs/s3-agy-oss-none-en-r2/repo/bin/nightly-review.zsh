#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="/tmp/h-AQpjbm/projects/shop"
OUT="/tmp/h-AQpjbm/Library/Logs/nightly-review-$(/bin/date +%F).md"
NOTIFY="/tmp/h-AQpjbm/bin/notify.sh"

SINCE=$(/bin/date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

claude -p "$PROMPT" --output-format text > "$OUT"
status=$?

if [ $status -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $status), see $OUT"
  exit $status
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
