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
echo "Run finished in ${SECONDS}s with exit code $rc" >&2

if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${SECONDS}s), see $OUT"
  exit $(( rc != 0 ? rc : 1 ))
fi

"$NOTIFY" "nightly review done (${SECONDS}s): $(head -c 300 "$OUT")"
