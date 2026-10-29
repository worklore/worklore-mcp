#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
STARTED_AT=$(date +%s)

fail() {
  local rc=$1
  shift
  local message="nightly review FAILED: $* (elapsed $(($(date +%s) - STARTED_AT))s)"
  print -u2 -- "$message"
  "$NOTIFY" "$message" || print -u2 -- "nightly review: failure notification failed"
  exit "$rc"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || fail 1 "repo missing: $REPO"

print -u2 -- "nightly review: started at $(date)"
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?

(( rc == 0 )) || fail "$rc" "claude exited $rc; see $OUT"
[[ -s "$OUT" ]] || fail 1 "claude returned no review; see $OUT"

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || {
  print -u2 -- "nightly review: success notification failed (elapsed $(($(date +%s) - STARTED_AT))s)"
  exit 1
}
print -u2 -- "nightly review: completed in $(($(date +%s) - STARTED_AT))s; review: $OUT"
