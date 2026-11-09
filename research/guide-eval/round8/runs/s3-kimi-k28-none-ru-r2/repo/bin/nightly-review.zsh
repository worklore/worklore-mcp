#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
LOGDIR="$HOME/Library/Logs"
OUT="$LOGDIR/nightly-review-$(date +%F).md"
CLAUDE_ERR="$LOGDIR/nightly-review-claude-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

mkdir -p "$LOGDIR"

claude -p "$PROMPT" --output-format text > "$OUT" 2> "$CLAUDE_ERR"
rc=$?

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc): $(head -c 200 "$CLAUDE_ERR")" \
    || echo "nightly-review: notify.sh failed" >&2
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" \
  || echo "nightly-review: notify.sh failed" >&2
