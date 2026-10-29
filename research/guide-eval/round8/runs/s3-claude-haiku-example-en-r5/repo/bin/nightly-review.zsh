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

# `status` is read-only in zsh (alias of $?), so use rc.
# stdin is closed: the prompt is an argument, and claude must not wait on stdin.
START=$SECONDS
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?
ELAPSED=$((SECONDS - START))
BYTES=$(wc -c < "$OUT" | tr -d ' ')
echo "$(date '+%F %T') claude exit=$rc seconds=$ELAPSED bytes=$BYTES"

# exit 0 with an empty output is also a failure.
if [ $rc -ne 0 ] || [ "$BYTES" -eq 0 ]; then
  "$NOTIFY" "nightly review FAILED (claude exit $rc, ${ELAPSED}s, $BYTES bytes), see $OUT"
  exit 1
fi

"$NOTIFY" "nightly review done (${ELAPSED}s): $(head -c 300 "$OUT")"
