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

start=$SECONDS

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing" || true; exit 1; }

print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?

print -r -- "nightly-review: claude exit=$rc after $((SECONDS - start))s at $(date '+%F %T')"

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT" \
    || print -u2 -- "nightly-review: notify.sh itself failed (rc=$?)"
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" \
  || { print -u2 -- "nightly-review: notify.sh itself failed (rc=$?)"; exit 1; }
