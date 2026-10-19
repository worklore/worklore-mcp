#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# Send a Telegram message; if that fails too, at least say so in the .err log.
notify() {
  "$NOTIFY" "$1" || print -u2 -- "$(date '+%F %T') notify.sh failed (rc=$?) for: $1"
}

print -u2 -- "$(date '+%F %T') nightly review start (USER=${USER:-unset} HOME=$HOME)"
START=$SECONDS

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

# Prompt on stdin: no reliance on multi-line argv, and claude never waits on an open stdin.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?   # never `status=`: in zsh $status is read-only and assigning to it kills the script
ELAPSED=$(( SECONDS - START ))
print -u2 -- "$(date '+%F %T') claude exited rc=$rc after ${ELAPSED}s"

if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc after ${ELAPSED}s), see $OUT and ~/Library/Logs/nightly-review.err"
  exit $rc
fi

# Exit 0 is not proof of work: an empty review means nothing happened.
if [[ ! -s "$OUT" ]]; then
  notify "nightly review FAILED: claude exited 0 after ${ELAPSED}s but $OUT is empty"
  exit 1
fi

notify "nightly review done (${ELAPSED}s): $(head -c 300 "$OUT")"
