#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
# Note: never assign to `status` here; in zsh it is a read-only special
# variable and the assignment aborts the script (that is what kept this job
# silent). Use `rc` instead.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

notify() {
  "$NOTIFY" "$1" || print -u2 -- "$(date '+%F %T') notify.sh failed (exit $?): $1"
}

print -u2 -- "$(date '+%F %T') nightly-review start (USER=${USER:-unset})"
START=$SECONDS

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing ($REPO)"; exit 1; }

# Prompt via stdin: no multi-line argument parsing, no waiting on stdin.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$ERR"
rc=$?
DUR=$(( SECONDS - START ))
print -u2 -- "$(date '+%F %T') claude exit $rc after ${DUR}s"
[ -s "$ERR" ] && cat "$ERR" >&2

if [ $rc -ne 0 ]; then
  notify "nightly review FAILED (exit $rc, ${DUR}s): $(head -c 300 "$ERR")"
  exit $rc
fi

# Exit 0 is not proof of work: an empty summary is a failure too.
if [ ! -s "$OUT" ]; then
  notify "nightly review FAILED: claude exited 0 after ${DUR}s but produced no output"
  exit 1
fi

notify "nightly review done (${DUR}s): $(head -c 300 "$OUT")"
