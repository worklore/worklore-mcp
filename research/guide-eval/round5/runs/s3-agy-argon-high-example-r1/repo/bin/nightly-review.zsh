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
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?
duration=$SECONDS
print -u2 "$(date +%FT%T) nightly-review finished in ${duration}s (exit $rc)"

if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${duration}s), see $OUT"
  exit $(( rc != 0 ? rc : 1 ))
fi

"$NOTIFY" "nightly review done (${duration}s): $(head -c 300 "$OUT")"
