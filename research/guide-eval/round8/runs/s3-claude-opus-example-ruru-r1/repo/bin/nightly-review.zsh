#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"
START=$(date +%s)

log() { print -r -- "$(date '+%F %T') nightly-review: $*" >&2; }

# Safety net: whatever kills the script (syntax/runtime error, signal,
# unexpected exit) still produces a message. Set notified=1 once a
# deliberate notification has been sent.
notified=0
notify() {
  notified=1
  log "notify: $1"
  "$NOTIFY" "$1"
  local nrc=$?
  if (( nrc != 0 )); then
    log "notify.sh FAILED (rc=$nrc)"
    # local fallback so the failure is visible on the Mac at least
    /usr/bin/osascript -e 'display notification "notify.sh failed, see ~/Library/Logs/nightly-review.err" with title "nightly review"' 2>/dev/null
  fi
}
on_exit() {
  local rc=$1
  log "exit rc=$rc after $(( $(date +%s) - START ))s"
  if (( ! notified )); then
    "$NOTIFY" "nightly review DIED unexpectedly (exit $rc), see ~/Library/Logs/nightly-review.err" \
      || log "notify.sh FAILED in exit trap"
  fi
}
# `trap ... EXIT`, not a TRAPEXIT function: the latter is inherited by $(...) subshells.
trap 'on_exit $?' EXIT

log "start (USER=${USER:-unset} HOME=$HOME)"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo $REPO missing"; exit 1; }

# Prompt via stdin, not as a multi-line argument.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$ERR"
rc=$?   # NOT `status`: in zsh that is a read-only builtin and assigning it kills the script
cat "$ERR" >&2
DUR=$(( $(date +%s) - START ))

if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc, ${DUR}s): $(tail -c 300 "$ERR")"
  exit $rc
fi
if [[ ! -s "$OUT" ]]; then
  notify "nightly review FAILED: exit 0 but empty output (${DUR}s), see $OUT"
  exit 1
fi

# The summary is at the end of the review, so send the tail.
notify "nightly review done (${DUR}s):
$(tail -n 5 "$OUT")"
