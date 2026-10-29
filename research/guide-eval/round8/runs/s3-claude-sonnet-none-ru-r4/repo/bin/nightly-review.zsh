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

ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
claude -p "$PROMPT" --output-format text > "$OUT" 2> "$ERR"
rc=$?  # not "status": it is read-only in zsh

if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc): $(head -c 200 "$ERR")"
  exit "${rc/#0/1}"
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
