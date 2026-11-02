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

# `status` is a read-only special parameter in zsh; assigning to it kills the
# script before the failure notice. Use rc. Close stdin so claude -p never waits on it.
claude -p "$PROMPT" --output-format text > "$OUT" 2>> "$OUT.err" < /dev/null
rc=$?

if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc): $(head -c 300 "$OUT.err" 2>/dev/null)"
  exit $(( rc ? rc : 1 ))
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
