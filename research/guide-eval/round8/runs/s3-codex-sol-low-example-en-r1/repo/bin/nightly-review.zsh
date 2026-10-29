#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?

if (( rc != 0 )); then
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
  exit $rc
fi

if [[ ! -s "$OUT" ]]; then
  "$NOTIFY" "nightly review FAILED (empty summary), see $OUT"
  exit 1
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
