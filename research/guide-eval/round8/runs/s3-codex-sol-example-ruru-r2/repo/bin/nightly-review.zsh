#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
STARTED_AT=$(date +%s)

finish_failure() {
  local reason="$1" exit_code="$2"
  local elapsed_seconds=$(( $(date +%s) - STARTED_AT ))
  print -u2 -- "nightly review FAILED: $reason (${elapsed_seconds}s)"
  if ! "$NOTIFY" "nightly review FAILED: $reason (${elapsed_seconds}s); see $OUT"; then
    print -u2 -- "nightly review: failure notification could not be sent"
  fi
  exit "$exit_code"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || finish_failure "repository missing: $REPO" 1

if claude -p "$PROMPT" --output-format text </dev/null > "$OUT"; then
  :
else
  rc=$?
  finish_failure "claude exited with code $rc" "$rc"
fi

[[ -s "$OUT" ]] || finish_failure "claude produced an empty review" 1

elapsed_seconds=$(( $(date +%s) - STARTED_AT ))
if "$NOTIFY" "nightly review done (${elapsed_seconds}s): $(head -c 300 "$OUT")"; then
  print -- "nightly review done (${elapsed_seconds}s): $OUT"
else
  rc=$?
  print -u2 -- "nightly review: success notification failed (exit $rc, ${elapsed_seconds}s)"
  exit "$rc"
fi
