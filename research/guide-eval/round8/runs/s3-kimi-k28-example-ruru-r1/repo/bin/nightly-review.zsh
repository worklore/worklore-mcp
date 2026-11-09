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
  "$NOTIFY" "$1" || print -u2 -- "nightly-review: notify.sh failed to send: $1"
}

start=$SECONDS

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?

if [ $rc -ne 0 ]; then
  notify "nightly review FAILED (exit $rc), see $OUT"
  exit $rc
fi

if [ ! -s "$OUT" ]; then
  notify "nightly review FAILED: claude exited 0 but wrote nothing to $OUT"
  exit 1
fi

print -u2 -- "nightly review finished in $(( SECONDS - start ))s"
notify "nightly review done: $(head -c 300 "$OUT")"
