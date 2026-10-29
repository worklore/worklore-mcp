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

START=$SECONDS
echo "$(date '+%F %T') nightly review start"

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# zsh treats `status` as a read-only variable: assigning to it kills the script,
# so the notifier below never ran. Use `rc`.
# </dev/null: the prompt is an argument, so claude must not wait on stdin.
claude -p "$PROMPT" --output-format text > "$OUT" < /dev/null
rc=$?
echo "$(date '+%F %T') claude exited $rc after $((SECONDS - START))s"

# exit 0 with no output is still a failure: nothing was reviewed.
if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
  exit 1
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
echo "$(date '+%F %T') nightly review done in $((SECONDS - START))s"
