#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u
started_at=$(date +%s)

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || {
  print -u2 "nightly review: repo missing: $REPO"
  "$NOTIFY" "nightly review: repo missing" || print -u2 "nightly review: failure notification failed"
  exit 1
}

claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?

if (( rc != 0 )); then
  print -u2 "nightly review: agent failed with exit $rc after $(($(date +%s) - started_at))s"
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT" || print -u2 "nightly review: failure notification failed"
  exit $rc
fi

if [[ ! -s "$OUT" ]]; then
  print -u2 "nightly review: agent returned empty output after $(($(date +%s) - started_at))s"
  "$NOTIFY" "nightly review FAILED (empty output), see $OUT" || print -u2 "nightly review: failure notification failed"
  exit 1
fi

print -r -- "nightly review: completed in $(($(date +%s) - started_at))s; output: $OUT"
"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || {
  print -u2 "nightly review: success notification failed"
  exit 1
}
