#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
STARTED_AT=$(date +%s)

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || {
  print -r -- "nightly review: repo missing: $REPO" >&2
  "$NOTIFY" "nightly review FAILED: repo missing: $REPO" || print -r -- "nightly review: failure notification failed" >&2
  exit 1
}

claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?
elapsed=$(( $(date +%s) - STARTED_AT ))

if (( rc != 0 )); then
  print -r -- "nightly review: agent failed with exit $rc after ${elapsed}s; output: $OUT" >&2
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT" || print -r -- "nightly review: failure notification failed" >&2
  exit "$rc"
fi

if [[ ! -s "$OUT" ]]; then
  print -r -- "nightly review: agent returned empty output after ${elapsed}s: $OUT" >&2
  "$NOTIFY" "nightly review FAILED (empty output), see $OUT" || print -r -- "nightly review: failure notification failed" >&2
  exit 1
fi

print -r -- "nightly review: completed in ${elapsed}s; output: $OUT" >&2
"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || {
  print -r -- "nightly review: success notification failed" >&2
  exit 1
}
