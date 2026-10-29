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

if claude -p "$PROMPT" --output-format text > "$OUT"; then
  if [[ ! -s "$OUT" ]]; then
    print -u2 -- "nightly review: claude produced no summary"
    "$NOTIFY" "nightly review FAILED: claude produced no summary, see $OUT"
    exit 1
  fi
else
  claude_status=$?
  print -u2 -- "nightly review: claude failed (exit $claude_status)"
  "$NOTIFY" "nightly review FAILED (exit $claude_status), see $OUT"
  exit $claude_status
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
