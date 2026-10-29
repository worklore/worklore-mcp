#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# Timestamped line in the stderr log, so each run is visible in nightly-review.err.
log() { print -r -- "$(date '+%F %T') $*" >&2; }

# Send a message; if the notifier itself fails, say so in the log instead of
# dying silently.
notify() {
  "$NOTIFY" "$1" || log "notify.sh failed (exit $?) for: ${1[1,80]}"
}

log "start (USER=${USER:-unset} HOME=$HOME)"
START=$SECONDS

cd "$REPO" || { log "repo missing: $REPO"; notify "nightly review: repo missing ($REPO)"; exit 1; }

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

# Prompt via stdin: no dependence on multi-line argument parsing, and claude
# never waits on an open stdin.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?   # NOT "status": in zsh it is a read-only special variable, assigning kills the script
ELAPSED=$(( SECONDS - START ))
log "claude exit $rc after ${ELAPSED}s, output $(wc -c < "$OUT" | tr -d ' ') bytes"

if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc, ${ELAPSED}s), see ~/Library/Logs/nightly-review.err"
  exit $rc
fi

# Exit 0 is not proof of work: an empty output means nothing was done.
if [[ ! -s "$OUT" ]]; then
  notify "nightly review FAILED: claude exited 0 but produced no output (${ELAPSED}s)"
  exit 2
fi

notify "nightly review done (${ELAPSED}s): $(head -c 300 "$OUT")"
log "done"
