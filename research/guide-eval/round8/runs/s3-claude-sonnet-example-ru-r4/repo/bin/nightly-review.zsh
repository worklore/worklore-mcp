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

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing" || echo "notify failed" >&2; exit 1; }

START=$SECONDS
# </dev/null: the prompt is an argument, don't let the CLI wait on stdin
claude -p "$PROMPT" --output-format text > "$OUT" </dev/null
rc=$?   # never assign to `status` in zsh: it is read-only
DUR=$((SECONDS - START))
echo "$(date '+%F %T') nightly-review rc=$rc duration=${DUR}s" >&2

if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${DUR}s), see $OUT" \
    || echo "notify failed" >&2
  exit ${${rc:#0}:-1}
fi

"$NOTIFY" "nightly review done in ${DUR}s: $(head -c 300 "$OUT")"
