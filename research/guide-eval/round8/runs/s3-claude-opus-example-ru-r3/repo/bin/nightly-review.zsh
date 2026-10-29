#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

log() { print -r -- "$(date '+%F %T') nightly-review: $*" >&2; }

# Never stay silent: if the notifier itself fails, at least leave a trace in the log.
notify() {
  "$NOTIFY" "$1" || log "notify.sh FAILED (exit $?) for message: $1"
}

log "start (USER=${USER:-<unset>} HOME=$HOME)"
START=$SECONDS

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { log "repo missing: $REPO"; notify "nightly review: repo missing ($REPO)"; exit 1; }

ERR_TMP=$(mktemp -t nightly-review) || ERR_TMP=/dev/null
# Prompt goes in via stdin: no hanging on an open stdin, no multi-line argument issues.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$ERR_TMP"
rc=$?   # NOT "status": in zsh it is a read-only special parameter, assigning to it kills the script
ELAPSED=$(( SECONDS - START ))
CLAUDE_ERR=$(head -c 300 "$ERR_TMP" 2>/dev/null)
cat "$ERR_TMP" >&2 2>/dev/null
[ "$ERR_TMP" != /dev/null ] && rm -f "$ERR_TMP"

log "claude exit=$rc after ${ELAPSED}s, output $(wc -c < "$OUT" | tr -d ' ') bytes"

if [ $rc -ne 0 ]; then
  notify "nightly review FAILED (exit $rc, ${ELAPSED}s): ${CLAUDE_ERR:-no stderr}. See $OUT and ~/Library/Logs/nightly-review.err"
  exit $rc
fi

# Exit 0 is not proof of work: an empty report is a failure too.
if [ ! -s "$OUT" ]; then
  notify "nightly review FAILED: claude exited 0 after ${ELAPSED}s but $OUT is empty"
  exit 1
fi

notify "nightly review done (${ELAPSED}s): $(head -c 300 "$OUT")"
log "done"
