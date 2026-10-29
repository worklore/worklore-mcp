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

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing" || true; exit 1; }

START=$SECONDS
# </dev/null: prompt is an argument, so don't let claude wait on stdin.
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?   # never assign to $status: read-only in zsh, kills the script
echo "nightly review: claude exit $rc after $((SECONDS - START))s"

# A "successful" run with empty output is still a failure.
if [ $rc -eq 0 ] && [ ! -s "$OUT" ]; then rc=2; fi

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT" || echo "notify failed" >&2
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || { echo "notify failed" >&2; exit 3; }
