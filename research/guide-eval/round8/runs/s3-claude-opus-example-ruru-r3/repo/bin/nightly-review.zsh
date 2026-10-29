#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# Every run leaves a timestamped trace in the launchd stderr log.
log() { print -r -- "$(date '+%F %T') $*" >&2; }

# Never fail silently: if the notifier itself fails, say so in the log.
notify() {
  "$NOTIFY" "$1" || log "notify.sh FAILED (rc=$?) for message: ${1[1,200]}"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

log "start (USER=${USER:-unset} HOME=$HOME)"

cd "$REPO" || { log "repo missing: $REPO"; notify "nightly review: repo missing"; exit 1; }

START=$SECONDS
# Prompt goes in via stdin; claude's stderr also lands in the launchd .err log.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?   # NOT "status": in zsh it is a read-only special parameter.
DUR=$(( SECONDS - START ))
log "claude exit=$rc duration=${DUR}s output_bytes=$(wc -c < "$OUT" | tr -d ' ')"

if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc, ${DUR}s), see $OUT and ~/Library/Logs/nightly-review.err"
  exit $rc
fi

# Exit 0 is not proof of work: an empty summary is a failure too.
if [[ ! -s "$OUT" ]]; then
  log "claude exited 0 but produced no output"
  notify "nightly review FAILED: empty output after ${DUR}s, see ~/Library/Logs/nightly-review.err"
  exit 1
fi

notify "nightly review done (${DUR}s): $(head -c 300 "$OUT")"
log "done"
