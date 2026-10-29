#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
START=$(date +%s)

fail() {
  local rc=$1
  shift
  print -u2 -- "nightly review: $* (after $(($(date +%s) - START))s)"
  "$NOTIFY" "nightly review FAILED: $*" || print -u2 -- "nightly review: failure notification failed"
  exit "$rc"
}

SINCE=$(date -v-1d +%F) || fail 1 "could not calculate review date"
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || fail 1 "repo missing: $REPO"

if claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"; then
  :
else
  rc=$?
  fail "$rc" "Claude exited with code $rc; see $OUT"
fi

[[ -s "$OUT" ]] || fail 1 "Claude produced no review; see $OUT"

print -u2 -- "nightly review: review written to $OUT (after $(($(date +%s) - START))s)"
"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || {
  rc=$?
  print -u2 -- "nightly review: success notification failed (exit $rc)"
  exit "$rc"
}
