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

claude -p "$PROMPT" --output-format text > "$OUT"
claude_exit=$?

if [ "$claude_exit" -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (Claude exit $claude_exit); see ~/Library/Logs/nightly-review.err" ||
    print -u2 "nightly review: failure notification could not be sent"
  exit "$claude_exit"
fi

if [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (Claude returned an empty review); see $OUT" ||
    print -u2 "nightly review: failure notification could not be sent"
  exit 1
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
