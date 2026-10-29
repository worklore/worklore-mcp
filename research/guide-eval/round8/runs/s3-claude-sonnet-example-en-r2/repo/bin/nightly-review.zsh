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

START=$SECONDS
# closed stdin so claude doesn't wait on it; never assign to `status` in zsh (read-only)
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?
DUR=$((SECONDS - START))
print -r -- "$(date '+%F %T') nightly-review rc=$rc duration=${DUR}s" >&2

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${DUR}s), see $OUT"
  exit $rc
fi

if [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review produced EMPTY output (${DUR}s)"
  exit 1
fi

"$NOTIFY" "nightly review done (${DUR}s): $(head -c 300 "$OUT")"
