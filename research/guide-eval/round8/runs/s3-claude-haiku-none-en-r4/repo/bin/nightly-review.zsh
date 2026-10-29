#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# Not `status`: that name is read-only in zsh, and the assignment aborts the script.
# stderr goes to its own file so errors such as "Not logged in" reach the failure message.
claude -p "$PROMPT" --output-format text > "$OUT" 2> "$ERR"
rc=$?

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc): $(head -c 300 "$ERR") (see $ERR)"
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
