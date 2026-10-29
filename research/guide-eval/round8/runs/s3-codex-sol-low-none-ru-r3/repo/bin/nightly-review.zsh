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

notify() {
  "$NOTIFY" "$1" || { print -u2 -- "nightly review: notification failed"; return 1; }
}

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

claude -p "$PROMPT" --output-format text > "$OUT" 2> "${OUT%.md}.err"
review_exit=$?

if [ "$review_exit" -ne 0 ]; then
  notify "nightly review FAILED (exit $review_exit), see $OUT and ${OUT%.md}.err"
  exit "$review_exit"
fi

notify "nightly review done: $(head -c 300 "$OUT")"
