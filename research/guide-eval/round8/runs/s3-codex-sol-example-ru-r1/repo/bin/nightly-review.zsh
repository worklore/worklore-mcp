#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
START=$(date +%s)

print -u2 -- "nightly review started at $(date)"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

if ! cd "$REPO"; then
  print -u2 -- "nightly review failed: repo missing: $REPO"
  "$NOTIFY" "nightly review FAILED: repo missing: $REPO"
  exit 1
fi

claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?

if (( rc != 0 )); then
  print -u2 -- "nightly review failed: claude exit $rc after $(($(date +%s) - START))s"
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
  exit $rc
fi

if [[ ! -s "$OUT" ]]; then
  print -u2 -- "nightly review failed: empty output after $(($(date +%s) - START))s"
  "$NOTIFY" "nightly review FAILED: empty output, see $OUT"
  exit 1
fi

if ! "$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"; then
  print -u2 -- "nightly review failed: notification after $(($(date +%s) - START))s"
  exit 1
fi

print -u2 -- "nightly review succeeded: $OUT after $(($(date +%s) - START))s"
