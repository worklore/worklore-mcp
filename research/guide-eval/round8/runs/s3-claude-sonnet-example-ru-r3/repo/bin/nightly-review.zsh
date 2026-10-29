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
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?   # not "status": it is read-only in zsh and kills the script
DUR=$((SECONDS - START))
echo "$(date '+%F %T') claude exit=$rc duration=${DUR}s"

# a run that "succeeds" with empty output or in a few seconds did no real work
if [ $rc -eq 0 ] && [ ! -s "$OUT" ]; then rc=2; fi

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${DUR}s), see $OUT"
  exit $rc
fi

"$NOTIFY" "nightly review done (${DUR}s): $(head -c 300 "$OUT")"
