#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
CLAUDE_ERR="$HOME/Library/Logs/nightly-review-$(date +%F).claude.err"
NOTIFY="$HOME/bin/notify.sh"
START=$SECONDS

log() { print -r -- "$(date '+%F %T') $*" >&2 }

notify() {
  "$NOTIFY" "$1" || log "notify.sh failed (exit $?), message was: $1"
}

# Safety net: any exit we did not plan for (a zsh error, an unexpected exit)
# still sends a failure note. Planned exits set DONE=1 first.
DONE=0
trap 'rc=$?; (( DONE )) || notify "nightly review FAILED unexpectedly (exit $rc, $(( SECONDS - START ))s), see ~/Library/Logs/nightly-review.err"' EXIT

fail() {
  log "FAILED: $1"
  DONE=1
  notify "nightly review FAILED: $1"
  exit 1
}

log "start (USER=${USER:-unset} HOME=$HOME)"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || fail "repo missing: $REPO"

# Prompt goes in via stdin: no multi-line argument, and claude never waits on
# an inherited stdin.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$CLAUDE_ERR"
rc=$?   # never `status=`: it is a read-only zsh builtin and kills the script
elapsed=$(( SECONDS - START ))
cat "$CLAUDE_ERR" >&2
log "claude exit $rc after ${elapsed}s, $(wc -c < "$OUT" | tr -d ' ') bytes in $OUT"

if (( rc != 0 )); then
  fail "claude exit $rc after ${elapsed}s: $(tail -n 3 "$CLAUDE_ERR" | head -c 500)"
fi
if [[ ! -s "$OUT" ]]; then
  fail "claude exit 0 but empty output after ${elapsed}s, see $OUT"
fi

# The prompt asks for the summary at the end, so send the tail, not the head.
summary=$(tail -n 5 "$OUT")
DONE=1
"$NOTIFY" "nightly review done (${elapsed}s):
${summary[1,1500]}" || { log "notify.sh failed on success message"; exit 1 }
log "done"
