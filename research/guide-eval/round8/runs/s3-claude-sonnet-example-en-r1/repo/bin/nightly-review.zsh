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
# </dev/null: prompt is an argument, don't let the CLI wait on stdin
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?   # never assign to $status: read-only in zsh
DUR=$((SECONDS - START))
echo "nightly-review: rc=$rc duration=${DUR}s out=$OUT" >&2

if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${DUR}s), see $OUT"
  if [ $rc -ne 0 ]; then exit $rc; else exit 1; fi
fi

"$NOTIFY" "nightly review done (${DUR}s): $(head -c 300 "$OUT")"
