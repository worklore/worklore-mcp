#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
DAY=$(date +%F)
OUT="$HOME/Library/Logs/nightly-review-$DAY.md"
ERR="$HOME/Library/Logs/nightly-review-$DAY.err"
NOTIFY="$HOME/bin/notify.sh"

# If the notifier itself fails, exit non-zero so launchd shows the failure.
notify() {
  "$NOTIFY" "$1" || { echo "notify failed: $1" >&2; exit 1; }
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

START=$(date +%s)
# < /dev/null: with the prompt passed as an argument, claude must not wait on stdin.
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT" 2> "$ERR"
rc=$?
cat "$ERR" >&2
SECS=$(( $(date +%s) - START ))
echo "$(date '+%F %T') rc=$rc secs=$SECS out_bytes=$(wc -c < "$OUT")"

# Exit 0 with no output is also a failure: it means the review did nothing.
if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  notify "nightly review FAILED (exit $rc, ${SECS}s): $(tail -c 300 "$ERR") $OUT"
  exit 1
fi

notify "nightly review done (${SECS}s): $(head -c 300 "$OUT")"
