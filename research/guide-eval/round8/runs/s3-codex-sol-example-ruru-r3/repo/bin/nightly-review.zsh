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

started=$SECONDS
if print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"; then
  if [[ ! -s "$OUT" ]]; then
    print -u2 -- "nightly review: claude exited successfully but wrote no review after $((SECONDS - started))s"
    "$NOTIFY" "nightly review FAILED: empty review, see $OUT"
    exit 1
  fi
else
  rc=$?
  print -u2 -- "nightly review: claude failed (exit $rc) after $((SECONDS - started))s"
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
  exit "$rc"
fi

print -u2 -- "nightly review: completed in $((SECONDS - started))s; review: $OUT"
"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
