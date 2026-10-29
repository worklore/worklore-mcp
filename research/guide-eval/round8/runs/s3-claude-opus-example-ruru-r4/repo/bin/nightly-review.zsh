#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
# NB: never assign to `status` here: in zsh it is a read-only builtin
# (same as $?), and assigning to it kills the script on the spot.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

log() { print -r -- "$(date '+%F %T') $*" >&2; }

notify() {
  if ! "$NOTIFY" "$1"; then
    log "notify.sh FAILED, message was: $1"
  fi
}

# Anything that kills the script before it reaches an explicit notify
# (e.g. an unexpected zsh error) still produces a failure message.
reported=0
on_exit() {
  if (( ! reported )); then
    notify "nightly review died unexpectedly (exit $1), see ~/Library/Logs/nightly-review.err"
  fi
}
trap 'on_exit $?' EXIT

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

if ! cd "$REPO"; then
  reported=1
  notify "nightly review: repo missing ($REPO)"
  exit 1
fi

log "start (USER=${USER:-unset})"
start=$SECONDS
# Prompt via stdin, not a multi-line argument.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$ERR"
rc=$?
dur=$(( SECONDS - start ))
log "claude exit=$rc duration=${dur}s"

if (( rc != 0 )) || [[ ! -s "$OUT" ]]; then
  reported=1
  notify "nightly review FAILED (exit $rc, ${dur}s): $(tail -c 300 "$ERR" 2>/dev/null)"
  (( rc != 0 )) && exit $rc || exit 1
fi

reported=1
notify "nightly review done (${dur}s): $(head -c 300 "$OUT")"
