#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# Every failure path goes through here, so it must not depend on anything
# that can fail before it. If Telegram itself fails, at least say so in the log.
notify() {
  "$NOTIFY" "$1" || print -u2 -- "$(date '+%F %T') notify.sh failed (exit $?): $1"
}

START=$SECONDS
print -u2 -- "$(date '+%F %T') nightly review start"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing ($REPO)"; exit 1; }

# Prompt via stdin: no multi-line argument parsing, and stdin is never left open.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?   # not "status": it is read-only in zsh and assigning to it kills the script
took=$(( SECONDS - START ))
print -u2 -- "$(date '+%F %T') claude exit $rc after ${took}s"

if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc after ${took}s), see $OUT and ~/Library/Logs/nightly-review.err"
  exit $rc
fi

# Exit 0 is not proof of work: require real output.
if [[ ! -s "$OUT" ]]; then
  notify "nightly review FAILED: claude exited 0 after ${took}s but $OUT is empty"
  exit 1
fi

notify "nightly review done (${took}s): $(head -c 300 "$OUT")"
