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

# NB: never assign to `status` in zsh (read-only builtin); use rc.
# Report failures loudly: also log to stderr if the notifier itself fails.
fail() {
  print -u2 -r -- "$(date '+%F %T') $1"
  "$NOTIFY" "$1" || print -u2 "notify.sh failed"
}

cd "$REPO" || { fail "nightly review: repo missing"; exit 1; }

START=$SECONDS
# Prompt goes via stdin, not a multi-line argument.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?
DUR=$((SECONDS - START))
print -r -- "$(date '+%F %T') claude rc=$rc duration=${DUR}s bytes=$(wc -c < "$OUT")"

if [ $rc -ne 0 ]; then
  fail "nightly review FAILED (exit $rc, ${DUR}s), see $OUT"
  exit $rc
fi

# Exit 0 is not proof of work: require real output.
if [ ! -s "$OUT" ]; then
  fail "nightly review produced EMPTY output (${DUR}s)"
  exit 2
fi

"$NOTIFY" "nightly review done (${DUR}s): $(head -c 300 "$OUT")"
