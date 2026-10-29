#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
STARTED=$(date +%s)

fail() {
  local rc=$1
  local message=$2
  printf 'nightly review FAILED: %s (exit %s, duration %ss)\n' "$message" "$rc" "$(($(date +%s) - STARTED))" >&2
  "$NOTIFY" "nightly review FAILED: $message (exit $rc), see $OUT" || \
    printf 'nightly review: failure notification also failed\n' >&2
  exit "$rc"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

printf 'nightly review started at %s\n' "$(date '+%Y-%m-%d %H:%M:%S')"
cd "$REPO" || fail 1 "repo missing: $REPO"

claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?

if (( rc != 0 )); then
  fail "$rc" "claude failed"
fi
[[ -s "$OUT" ]] || fail 1 "claude produced no review"

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || fail 1 "success notification failed"
printf 'nightly review completed (duration %ss, output %s)\n' "$(($(date +%s) - STARTED))" "$OUT"
