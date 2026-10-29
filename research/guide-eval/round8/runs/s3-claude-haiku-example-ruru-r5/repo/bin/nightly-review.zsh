#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERRF="$HOME/Library/Logs/nightly-review-$(date +%F).stderr"
NOTIFY="$HOME/bin/notify.sh"
START=$SECONDS

# Any non-zero exit notifies, including early deaths like a read-only
# variable error. Explicit paths below only exit; they never notify twice.
finish() {
  local rc=$?
  if [ $rc -ne 0 ]; then
    local reason=$(head -c 200 "$ERRF" 2> /dev/null)
    "$NOTIFY" "nightly review FAILED (exit $rc after $((SECONDS - START))s): ${reason:-no stderr}"
  fi
}
trap finish EXIT

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

echo "$(date '+%F %T') start, since $SINCE"

cd "$REPO" || { echo "repo missing: $REPO" >&2; exit 1; }

claude -p "$PROMPT" --output-format text < /dev/null > "$OUT" 2> "$ERRF"
rc=$?
echo "$(date '+%F %T') claude exit $rc after $((SECONDS - START))s"
[ $rc -eq 0 ] || exit $rc

# Exit 0 with no output is not a success either.
if [ ! -s "$OUT" ]; then
  echo "empty output in $OUT" >&2
  exit 1
fi

"$NOTIFY" "nightly review done in $((SECONDS - START))s: $(head -c 300 "$OUT")"
