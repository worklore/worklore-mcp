#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

start=$(date +%s)
REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
RUNLOG="$HOME/Library/Logs/nightly-review.out"

# Any non-zero exit must produce a failure note; silence must be impossible.
trap 'rc=$?
print -r -- "$(date +%FT%T) exit=$rc duration=$(( $(date +%s) - start ))s" >> "$RUNLOG"
if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
fi
exit $rc' EXIT

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || exit 1

print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?

if [ $rc -ne 0 ]; then
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
