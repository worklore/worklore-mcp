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

# Anything that goes wrong below must still reach the phone, so report first, then exit.
fail() {
  echo "$(date '+%F %T') FAILED: $1" >&2
  "$NOTIFY" "nightly review FAILED: $1" || echo "$(date '+%F %T') notify also failed" >&2
  exit 1
}

echo "$(date '+%F %T') start, since $SINCE"
started=$(date +%s)

cd "$REPO" || fail "repo missing ($REPO)"

# Not `status`: that is a read-only special parameter in zsh, and assigning to it kills the script.
claude -p "$PROMPT" --output-format text > "$OUT"
rc=$?

echo "$(date '+%F %T') claude exit=$rc after $(( $(date +%s) - started ))s"

if [ $rc -ne 0 ]; then
  fail "claude exit $rc, see $OUT"
fi

# Exit 0 with no output means nothing was reviewed.
if [ ! -s "$OUT" ]; then
  fail "claude exit 0 but $OUT is empty"
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || fail "notify.sh failed after a successful review, see $OUT"
echo "$(date '+%F %T') done"
