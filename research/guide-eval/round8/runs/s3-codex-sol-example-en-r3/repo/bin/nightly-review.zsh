#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

STARTED_AT=$(date +%s)
REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

fail() {
  local rc=$1 message=$2
  print -u2 -- "$message (after $(($(date +%s) - STARTED_AT))s)"
  "$NOTIFY" "$message" || print -u2 -- "nightly review: failure notification failed"
  exit "$rc"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || fail 1 "nightly review FAILED: repo missing ($REPO)"

claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?

(( rc == 0 )) || fail "$rc" "nightly review FAILED (exit $rc), see $OUT"
[[ -s "$OUT" ]] || fail 1 "nightly review FAILED: empty summary, see $OUT"

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || {
  print -u2 -- "nightly review: success notification failed"
  exit 1
}
print -u2 -- "nightly review succeeded in $(($(date +%s) - STARTED_AT))s; summary: $OUT"
