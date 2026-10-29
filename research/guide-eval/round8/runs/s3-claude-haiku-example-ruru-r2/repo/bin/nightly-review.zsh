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

START=$(date +%s)
echo "$(date '+%F %T') start"

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# Prompt goes through stdin, not argv: no multi-line argument parsing, and claude never waits on an open stdin.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
# Not `status`: it is read-only in zsh, and that assignment used to kill the script before any notification.
rc=$?
DURATION=$(( $(date +%s) - START ))
echo "$(date '+%F %T') claude exit=$rc duration=${DURATION}s"

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc after ${DURATION}s), see $OUT"
  exit $rc
fi

# Exit 0 is not proof of work: an empty summary is a failure too.
if [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review: claude exited 0 but $OUT is empty (after ${DURATION}s)"
  exit 1
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
