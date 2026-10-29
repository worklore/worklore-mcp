#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

if claude -p "$PROMPT" --output-format text > "$OUT" 2> "$ERR"; then
  "$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
else
  claude_exit=$?
  reason=$(head -c 300 "$ERR")
  "$NOTIFY" "nightly review FAILED (exit $claude_exit): $reason (see $ERR)"
  exit "$claude_exit"
fi
