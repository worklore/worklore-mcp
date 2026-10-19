#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

RUN_START=$(date +%s)
TRAPEXIT() {
  print -u2 -- "nightly review duration: $(($(date +%s) - RUN_START))s"
}

REPO="${NIGHTLY_REPO:-$HOME/projects/shop}"
OUT="${NIGHTLY_OUT:-$HOME/Library/Logs/nightly-review-$(date +%F).md}"
NOTIFY="${NIGHTLY_NOTIFY:-$HOME/bin/notify.sh}"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || {
  print -u2 -- "nightly review: repo missing: $REPO"
  "$NOTIFY" "nightly review FAILED: repo missing: $REPO"
  exit 1
}

print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?

if (( rc != 0 )); then
  print -u2 -- "nightly review: agent failed (exit $rc)"
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT"
  exit $rc
fi

if [[ ! -s "$OUT" ]]; then
  print -u2 -- "nightly review: agent produced an empty review"
  "$NOTIFY" "nightly review FAILED: empty review, see $OUT"
  exit 1
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
