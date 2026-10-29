#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
SECONDS=0

fail() {
  local rc=$1 message=$2 notify_rc
  print -u2 -- "nightly review: $message (duration ${SECONDS}s)"
  if "$NOTIFY" "nightly review FAILED: $message"; then
    :
  else
    notify_rc=$?
    print -u2 -- "nightly review: failure notification failed (exit $notify_rc)"
  fi
  exit "$rc"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || fail 1 "repo missing: $REPO"

if claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"; then
  if [[ ! -s "$OUT" ]]; then
    fail 1 "agent produced no summary; see $OUT"
  fi
else
  rc=$?
  fail "$rc" "agent exited $rc; see $OUT"
fi

if "$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"; then
  print -u2 -- "nightly review: summary sent (duration ${SECONDS}s; output $OUT)"
else
  rc=$?
  print -u2 -- "nightly review: success notification failed (exit $rc; duration ${SECONDS}s; output $OUT)"
  exit "$rc"
fi
