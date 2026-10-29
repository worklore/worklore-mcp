#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
LOG="$HOME/Library/Logs/nightly-review.log"

start=$(date +%s)

# Every run leaves a line in LOG, so "did it run, how long, how did it end"
# is answerable even when Telegram says nothing.
log() {
  print -r -- "$(date '+%F %T') $*" >> "$LOG"
}

# A failed notify must not vanish silently: say so on stderr and exit nonzero.
notify() {
  "$NOTIFY" "$1" || { print -r -- "notify.sh failed for: $1" >&2; exit 1; }
}

# Failure path: log and notify first, before anything else can go wrong.
fail() {
  local rc=$1 msg=$2
  log "FAILED rc=$rc after $(( $(date +%s) - start ))s: $msg"
  notify "nightly review FAILED (exit $rc): $msg"
  exit "$rc"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || fail 1 "repo missing: $REPO"

# stdin from /dev/null so the CLI never waits for input under launchd.
claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"
rc=$?

if [ $rc -ne 0 ]; then
  fail $rc "claude exited $rc, see $OUT and nightly-review.err"
fi

# Exit 0 with no output is still a failure: nothing was reviewed.
if [ ! -s "$OUT" ]; then
  fail 1 "claude exited 0 but $OUT is empty"
fi

log "OK after $(( $(date +%s) - start ))s, $(wc -l < "$OUT" | tr -d ' ') lines in $OUT"
notify "nightly review done: $(head -c 300 "$OUT")"
