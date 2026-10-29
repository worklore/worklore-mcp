#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

START=$(date +%s)
REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

fail() {
  local rc=$1
  local message=$2
  print -u2 -- "$message (elapsed $(( $(date +%s) - START ))s)"
  "$NOTIFY" "$message" || print -u2 -- "nightly review: failure notification failed"
  exit "$rc"
}

cd "$REPO" || fail 1 "nightly review FAILED: repo missing"

if print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"; then
  :
else
  rc=$?
  fail "$rc" "nightly review FAILED (agent exit $rc), see $OUT"
fi

grep -q '[^[:space:]]' "$OUT" || fail 1 "nightly review FAILED: empty review, see $OUT"

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || {
  print -u2 -- "nightly review: success notification failed"
  exit 1
}
print -- "nightly review completed (elapsed $(( $(date +%s) - START ))s): $OUT"
