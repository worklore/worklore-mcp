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

echo "$(date '+%F %T') start" >&2
start=$SECONDS

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# Prompt via stdin: no multi-line argument parsing, and claude never waits on an open stdin.
# NB: `status` is a read-only special variable in zsh; assigning to it kills the script.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?

echo "$(date '+%F %T') claude exit $rc after $((SECONDS - start))s" >&2

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT and ~/Library/Logs/nightly-review.err" \
    || echo "notify failed too" >&2
  exit $rc
fi

if [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED: claude exited 0 but $OUT is empty" || echo "notify failed too" >&2
  exit 1
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
