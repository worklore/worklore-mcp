#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
START=$SECONDS

log() { print -r -- "$(date '+%F %T') $*"; }

# Every failure goes through here. Do not assign to `status` in zsh: it is read-only.
fail() {
  log "FAILED after $((SECONDS - START))s: $1"
  "$NOTIFY" "nightly review FAILED: $1" || log "could not send failure note (notify exit $?)"
  exit 1
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

log "start, reviewing commits since $SINCE"

cd "$REPO" || fail "repo missing at $REPO"

# < /dev/null: claude -p can wait on stdin even when the prompt is an argument.
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?

if [ $rc -ne 0 ]; then
  fail "claude exit $rc, see $OUT"
fi
# An exit code of 0 with no output means nothing was done.
if [ ! -s "$OUT" ]; then
  fail "claude exited 0 but $OUT is empty"
fi

log "claude ok in $((SECONDS - START))s, $(wc -c < "$OUT" | tr -d ' ') bytes"
"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || { log "could not send summary note"; exit 1; }
log "done"
