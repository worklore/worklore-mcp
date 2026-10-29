#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
DAY=$(date +%F)
OUT="$HOME/Library/Logs/nightly-review-$DAY.md"
ERR="$HOME/Library/Logs/nightly-review-$DAY.err"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

# Runs on every exit. Any non-zero exit, including an abort in the middle of
# the script, gets a Telegram note. Without this, a crash before the explicit
# failure branch is silent.
finish() {
  local rc=$?
  if [ $rc -ne 0 ]; then
    "$NOTIFY" "nightly review FAILED (exit $rc): $(head -c 300 "$ERR" 2>/dev/null)" || true
  fi
}
trap finish EXIT

cd "$REPO" || exit 1

# Not named `status`: that is a read-only special parameter in zsh (same as $?),
# and the assignment aborted the script before anything was reported.
claude -p "$PROMPT" --output-format text > "$OUT" 2> "$ERR"
claude_rc=$?
if [ $claude_rc -ne 0 ]; then
  exit $claude_rc
fi

if [ ! -s "$OUT" ]; then
  echo "claude exited 0 but wrote no output to $OUT" >> "$ERR"
  exit 2
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
