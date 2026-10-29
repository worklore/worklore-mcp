#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="${NIGHTLY_REPO:-$HOME/projects/shop}"
NOTIFY="${NIGHTLY_NOTIFY:-$HOME/bin/notify.sh}"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err.txt"

notify() {
  # A failed notification must not hide the real result.
  "$NOTIFY" "$1" || print -u2 -- "$(date '+%F %T') notify failed"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

print -- "$(date '+%F %T') start"
START=$(date +%s)

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

# Prompt goes via stdin, not as an argument: claude -p reads stdin when no prompt argument is given.
# `rc`, not `status`: zsh makes `status` a read-only variable and the assignment kills the script.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$ERR"
rc=$?
DURATION=$(( $(date +%s) - START ))
print -- "$(date '+%F %T') claude exit=$rc duration=${DURATION}s"

if [ $rc -ne 0 ]; then
  cat "$ERR" >&2
  notify "nightly review FAILED (exit $rc after ${DURATION}s), see $ERR"
  exit $rc
fi

if [ ! -s "$OUT" ]; then
  notify "nightly review: empty output after ${DURATION}s, see $OUT"
  exit 1
fi

notify "nightly review done: $(head -c 300 "$OUT")"
