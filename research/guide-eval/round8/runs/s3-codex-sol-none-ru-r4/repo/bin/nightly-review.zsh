#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

notify_failure() {
  if ! "$NOTIFY" "nightly review FAILED: $1"; then
    print -u2 -- "nightly review: could not send failure notification"
  fi
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

if ! cd "$REPO"; then
  notify_failure "repo missing: $REPO"
  exit 1
fi

if claude -p "$PROMPT" --output-format text > "$OUT"; then
  :
else
  review_exit=$?
  notify_failure "claude exited $review_exit; see $OUT and nightly-review.err"
  exit "$review_exit"
fi

if [[ ! -s "$OUT" ]]; then
  notify_failure "claude produced an empty summary; see nightly-review.err"
  exit 1
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
