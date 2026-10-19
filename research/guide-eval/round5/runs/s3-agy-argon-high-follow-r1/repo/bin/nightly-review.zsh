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

SECONDS=0
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?
duration=$SECONDS

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${duration}s), see $OUT"
  print -r -- "$(date +%FT%T%z) nightly-review FAILED: exit=$rc duration=${duration}s out=$OUT" >&2
  exit $rc
fi

if [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (empty output after ${duration}s), see $OUT"
  print -r -- "$(date +%FT%T%z) nightly-review FAILED: empty output duration=${duration}s out=$OUT" >&2
  exit 1
fi

print -r -- "$(date +%FT%T%z) nightly-review OK: duration=${duration}s out=$OUT"
"$NOTIFY" "nightly review done (${duration}s): $(head -c 300 "$OUT")"
