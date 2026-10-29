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

# zsh reserves `status` (read-only), so use `rc` for exit codes.
echo "$(date '+%F %T') start" >&2
START=$(date +%s)

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# < /dev/null: headless claude must never wait on stdin under launchd.
claude -p "$PROMPT" --output-format text > "$OUT" < /dev/null
rc=$?
echo "$(date '+%F %T') claude exit=$rc duration=$(( $(date +%s) - START ))s" >&2

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
  exit $rc
fi

# Exit 0 with no output is still a failure: check the real outcome.
if [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (empty output), see $OUT"
  exit 1
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
