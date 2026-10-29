#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
LOGS="$HOME/Library/Logs"
OUT="$LOGS/nightly-review-$(date +%F).md"
ERR="$LOGS/nightly-review-$(date +%F).err"
RUNLOG="$LOGS/nightly-review-runs.log"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# zsh reserves `status` (read-only alias of $?), so use rc. Keep the failure
# check directly after the agent call so nothing can sit between failure and report.
START=$SECONDS
claude -p "$PROMPT" --output-format text > "$OUT" 2> "$ERR" < /dev/null
rc=$?
ELAPSED=$(( SECONDS - START ))
print -r -- "$(date '+%F %T') rc=$rc seconds=$ELAPSED bytes=$(wc -c < "$OUT" | tr -d ' ')" >> "$RUNLOG"

# An empty report is a failure too: exit 0 with nothing done must not look like success.
if (( rc != 0 )) || [[ ! -s "$OUT" ]]; then
  "$NOTIFY" "nightly review FAILED (rc $rc, ${ELAPSED}s), see $ERR: $(tail -c 300 "$ERR")" || exit 1
  exit $(( rc ? rc : 1 ))
fi

"$NOTIFY" "nightly review done (${ELAPSED}s): $(head -c 300 "$OUT")" || exit 1
