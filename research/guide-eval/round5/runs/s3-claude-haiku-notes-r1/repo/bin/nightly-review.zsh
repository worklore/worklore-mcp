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

started=$(date +%s)

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# `status` is a read-only special parameter in zsh (it is $?), so use rc.
# < /dev/null: claude -p must not wait on stdin under launchd.
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?
elapsed=$(( $(date +%s) - started ))

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc after ${elapsed}s), see $OUT and ~/Library/Logs/nightly-review.err"
  exit $rc
fi

if [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (empty output after ${elapsed}s), see $OUT"
  exit 1
fi

"$NOTIFY" "nightly review done in ${elapsed}s: $(head -c 300 "$OUT")"
