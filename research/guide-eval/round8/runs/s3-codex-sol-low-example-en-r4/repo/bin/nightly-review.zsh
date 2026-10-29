#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
START_SECONDS=$SECONDS

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?

if (( rc != 0 )); then
  print -r -- "nightly review failed: claude exit $rc after $(( SECONDS - START_SECONDS ))s" >&2
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
  exit $rc
fi

if [[ ! -s "$OUT" ]]; then
  print -r -- "nightly review failed: empty output after $(( SECONDS - START_SECONDS ))s" >&2
  "$NOTIFY" "nightly review FAILED (empty output), see $OUT"
  exit 1
fi

print -r -- "nightly review completed in $(( SECONDS - START_SECONDS ))s: $OUT"
"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
