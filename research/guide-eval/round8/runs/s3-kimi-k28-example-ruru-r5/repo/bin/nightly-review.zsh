#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
LOGDIR="$HOME/Library/Logs"
OUT="$LOGDIR/nightly-review-$(date +%F).md"
ERR="$LOGDIR/nightly-review.err"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

echo "nightly-review: start $(date '+%F %T')"
SECONDS=0

print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?

echo "nightly-review: claude exited rc=$rc after ${SECONDS}s"

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc) after ${SECONDS}s, see $OUT and $ERR"
  exit $rc
fi

"$NOTIFY" "nightly review done in ${SECONDS}s: $(head -c 300 "$OUT")"
