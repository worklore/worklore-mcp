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

notify() { "$NOTIFY" "$1" || print -u2 -- "notify failed: $1"; }
cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

# Never assign to `status` in zsh (read-only); use rc. Closed stdin so the CLI
# does not wait on it.
START=$SECONDS
claude -p "$PROMPT" --output-format text > "$OUT" < /dev/null
rc=$?
print -u2 -- "$(date '+%F %T') run took $((SECONDS - START))s, rc=$rc"

if [ $rc -ne 0 ]; then
  notify "nightly review FAILED (exit $rc), see $OUT"
  exit $rc
fi

# Exit 0 is not proof of work: require real output.
if [ ! -s "$OUT" ]; then
  notify "nightly review FAILED: empty output in $OUT"
  exit 1
fi

notify "nightly review done: $(head -c 300 "$OUT")"
