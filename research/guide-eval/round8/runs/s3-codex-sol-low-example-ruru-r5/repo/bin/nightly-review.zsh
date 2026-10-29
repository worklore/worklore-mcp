#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
STARTED=$(date +%s)

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review FAILED: repo missing ($REPO)"; exit 1; }

print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?
elapsed=$(( $(date +%s) - STARTED ))
print -r -- "nightly review: agent exit $rc after ${elapsed}s; output $OUT" >&2

if (( rc != 0 )); then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${elapsed}s), see $OUT" || print -r -- "nightly review: failure notification failed" >&2
  exit $rc
fi

if [[ ! -s "$OUT" ]]; then
  print -r -- "nightly review: agent produced no output" >&2
  "$NOTIFY" "nightly review FAILED: empty output after ${elapsed}s, see $OUT" || print -r -- "nightly review: failure notification failed" >&2
  exit 1
fi

"$NOTIFY" "nightly review done (${elapsed}s): $(head -c 300 "$OUT")"
