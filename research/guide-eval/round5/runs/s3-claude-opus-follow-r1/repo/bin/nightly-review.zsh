#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
START=$(date +%s)

# Failure reporter first: any non-zero exit (including zsh dying on an error)
# sends a Telegram note. Never assign to `status` in zsh — it is read-only.
notified=0
fail() {
  local msg="nightly review FAILED: $1 (after $(( $(date +%s) - START ))s), see $OUT and ~/Library/Logs/nightly-review.err"
  print -r -- "$(date '+%F %T') $msg" >&2
  "$NOTIFY" "$msg" || print -r -- "notify.sh failed too" >&2
  notified=1
  exit 1
}
TRAPEXIT() {
  local rc=$?
  if (( rc != 0 && ! notified )); then
    "$NOTIFY" "nightly review FAILED: script died (exit $rc), see ~/Library/Logs/nightly-review.err" \
      || print -r -- "notify.sh failed too" >&2
  fi
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || fail "repo $REPO missing"

print -r -- "$(date '+%F %T') start" >&2
# Prompt via stdin, not as a multi-line argument.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?
DUR=$(( $(date +%s) - START ))
print -r -- "$(date '+%F %T') claude exit $rc after ${DUR}s" >&2

(( rc == 0 )) || fail "claude exit $rc"
# Exit 0 is not proof of work: require real output and a plausible duration.
[[ -s "$OUT" ]] || fail "claude exited 0 but produced no output"
(( DUR >= 10 )) || fail "claude finished in ${DUR}s, too fast to have reviewed anything"

"$NOTIFY" "nightly review done in ${DUR}s: $(head -c 300 "$OUT")" || fail "could not send summary"
