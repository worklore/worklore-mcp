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

# Never fail silently: if the notifier itself fails, say so in the .err log.
notify() {
  "$NOTIFY" "$1" || print -u2 -r -- "$(date '+%F %T') notify.sh failed, message not sent: $1"
}

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

# `rc`, not `status`: zsh made `status` read-only and the assignment killed the script.
# </dev/null: a headless CLI given the prompt as an argument must not wait on stdin.
started=$(date +%s)
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?
print -r -- "$(date '+%F %T') claude exit=$rc duration=$(( $(date +%s) - started ))s out=$OUT" >&2

# Exit 0 with empty output is also a failure (the run did no work).
if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  notify "nightly review FAILED (exit $rc, output $([ -s "$OUT" ] && echo ok || echo empty)), see $OUT and nightly-review.err"
  exit $(( rc ? rc : 1 ))
fi

notify "nightly review done: $(head -c 300 "$OUT")"
