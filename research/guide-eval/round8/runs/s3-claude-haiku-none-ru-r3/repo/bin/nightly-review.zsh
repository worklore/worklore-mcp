#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
DAY=$(date +%F)
OUT="$HOME/Library/Logs/nightly-review-$DAY.md"
ERR="$HOME/Library/Logs/nightly-review-$DAY.stderr"
NOTIFY="$HOME/bin/notify.sh"

# A failed notification must not be silent: launchd keeps stderr in nightly-review.err.
notify() {
  "$NOTIFY" "$1" || print -u2 "nightly review: could not send Telegram message: $1"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing ($REPO)"; exit 1; }

# `status` is a read-only special parameter in zsh (it aliases $?), so use `rc`.
claude -p "$PROMPT" --output-format text > "$OUT" 2> "$ERR"
rc=$?
cat "$ERR" >&2

# Exit 0 with empty output is also a failure (e.g. "Not logged in" on some versions).
if [ $rc -eq 0 ] && [ ! -s "$OUT" ]; then
  rc=1
fi

if [ $rc -ne 0 ]; then
  reason=$(head -c 300 "$ERR")
  notify "nightly review FAILED (exit $rc): ${reason:-no output}. See $OUT and $ERR"
  exit $rc
fi

notify "nightly review done: $(head -c 300 "$OUT")"
