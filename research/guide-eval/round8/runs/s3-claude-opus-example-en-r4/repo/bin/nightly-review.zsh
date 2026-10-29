#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
START=$SECONDS
echo "$(date '+%F %T') start (USER=${USER:-unset})" >&2

# Safety net: if the script dies anywhere before reporting, still say so.
reported=0
zshexit() {
  local rc=$?
  if (( ! reported )); then
    "$NOTIFY" "nightly review DIED unexpectedly (exit $rc) after $((SECONDS - START))s, see ~/Library/Logs/nightly-review.err" \
      || echo "notify failed too" >&2
  fi
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

if ! cd "$REPO"; then
  reported=1
  "$NOTIFY" "nightly review: repo missing"
  exit 1
fi

# Prompt arrives as an argument; give claude a closed stdin so it never waits on it.
claude -p "$PROMPT" --output-format text > "$OUT" < /dev/null
rc=$?   # NOT `status`: in zsh that is a read-only special variable.
elapsed=$((SECONDS - START))
echo "$(date '+%F %T') claude exit $rc after ${elapsed}s" >&2

if (( rc != 0 )); then
  reported=1
  "$NOTIFY" "nightly review FAILED (exit $rc, ${elapsed}s): $(tail -c 200 "$HOME/Library/Logs/nightly-review.err")"
  exit $rc
fi

# A green exit with no output is still a failure.
if [[ ! -s "$OUT" ]]; then
  reported=1
  "$NOTIFY" "nightly review FAILED: claude exited 0 after ${elapsed}s but $OUT is empty"
  exit 1
fi

reported=1
"$NOTIFY" "nightly review done (${elapsed}s): $(head -c 300 "$OUT")"
