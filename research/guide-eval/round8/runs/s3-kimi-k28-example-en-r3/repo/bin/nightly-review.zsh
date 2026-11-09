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

start=$SECONDS

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?

if [ $rc -ne 0 ]; then
  print -r -- "[nightly-review] FAILED (exit $rc) after $((SECONDS - start))s, see $OUT"
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
  exit $rc
fi

print -r -- "[nightly-review] OK in $((SECONDS - start))s, wrote $OUT"
"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
