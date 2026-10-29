#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u
STARTED=$(date +%s)

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

print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?
elapsed=$(( $(date +%s) - STARTED ))
print -r -- "nightly review: agent exit=$rc, duration=${elapsed}s, output=$OUT" >&2

if (( rc != 0 )); then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${elapsed}s), see $OUT"
  exit $rc
fi

if [[ ! -s "$OUT" ]]; then
  "$NOTIFY" "nightly review FAILED (empty output, ${elapsed}s), see $OUT"
  exit 1
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
