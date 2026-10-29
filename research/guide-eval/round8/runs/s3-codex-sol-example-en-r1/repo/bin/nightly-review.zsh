#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

STARTED_AT=$(date +%s)
REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

log_result() {
  print -r -- "nightly review: $1 (duration $(($(date +%s) - STARTED_AT))s)" >&2
}

notify() {
  "$NOTIFY" "$1"
  local notify_rc=$?
  if (( notify_rc != 0 )); then
    print -r -- "nightly review: notification failed (exit $notify_rc)" >&2
  fi
  return "$notify_rc"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

if ! cd "$REPO"; then
  log_result "repo missing: $REPO"
  notify "nightly review FAILED: repo missing: $REPO"
  exit 1
fi

claude -p "$PROMPT" --output-format text </dev/null > "$OUT"
rc=$?

if (( rc != 0 )); then
  log_result "agent failed (exit $rc)"
  notify "nightly review FAILED (agent exit $rc), see $OUT"
  exit "$rc"
fi

if [[ ! -s "$OUT" ]]; then
  log_result "agent produced an empty summary"
  notify "nightly review FAILED: empty summary, see $OUT"
  exit 1
fi

if notify "nightly review done: $(head -c 300 "$OUT")"; then
  log_result "completed"
  exit 0
else
  rc=$?
  log_result "summary ready; notification failed (exit $rc)"
  exit "$rc"
fi
