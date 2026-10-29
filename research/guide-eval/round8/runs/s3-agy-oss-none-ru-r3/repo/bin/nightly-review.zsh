#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

# Use absolute paths for the current user
REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(/bin/date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# Use BSD date via full path to avoid GNU date issues
SINCE=$(/bin/date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# Run claude and capture output
claude -p "$PROMPT" --output-format text > "$OUT"
exit_code=$?

if [ $exit_code -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $exit_code), see $OUT"
  exit $exit_code
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
