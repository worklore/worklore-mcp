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

START=$(date +%s)
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
# not `status`: it is read-only in zsh and assigning to it kills the script
rc=$?
DURATION=$(( $(date +%s) - START ))
echo "$(date -Iseconds) claude exit=$rc duration=${DURATION}s out=$OUT"

# exit 0 with an empty summary still counts as a failure
if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${DURATION}s), see $OUT"
  exit 1
fi

"$NOTIFY" "nightly review done (${DURATION}s): $(head -c 300 "$OUT")"
