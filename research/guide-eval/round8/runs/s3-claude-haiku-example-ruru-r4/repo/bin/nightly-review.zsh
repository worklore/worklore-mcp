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

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# `status` is a read-only variable in zsh, so use `rc`.
# The prompt goes through stdin: passing a multi-line argument from a launchd job is fragile.
started=$(date +%s)
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?
elapsed=$(( $(date +%s) - started ))
print "$(date -Iseconds) exit=$rc elapsed=${elapsed}s out=$OUT"

# Exit 0 with an empty report is also a failure.
if [ $rc -ne 0 ] || [ ! -s "$OUT" ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${elapsed}s), see $OUT" || print -u2 "telegram notify failed"
  exit 1
fi

"$NOTIFY" "nightly review done (${elapsed}s): $(head -c 300 "$OUT")" || print -u2 "telegram notify failed"
