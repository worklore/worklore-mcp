#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

# A failing notifier must never mask the job's own result.
notify() { "$NOTIFY" "$1" || print -u2 -- "notify failed (exit $?)"; }

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

START=$SECONDS
# Prompt via stdin (no stdin wait / no argument parsing). NB: never assign to
# `status` in zsh, it is read-only -- use rc.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=${pipestatus[2]}
DUR=$((SECONDS - START))
print -u2 -- "$(date '+%F %T') run finished: rc=$rc duration=${DUR}s"

if [ $rc -ne 0 ]; then
  notify "nightly review FAILED (exit $rc, ${DUR}s), see $OUT"
  exit $rc
fi

if [ ! -s "$OUT" ]; then
  notify "nightly review FAILED: empty output (${DUR}s), see $OUT"
  exit 1
fi

notify "nightly review done (${DUR}s): $(head -c 300 "$OUT")"
