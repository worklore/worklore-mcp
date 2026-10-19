#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

notify() {
  "$NOTIFY" "$1" || print -u2 -- "$(date '+%F %T') notify.sh failed (exit $?): $1"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

start=$SECONDS
# Prompt via stdin: no multi-line argv parsing, and claude never waits on an open stdin.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?   # never `status=`: it is a read-only zsh builtin and assigning to it kills the script
elapsed=$(( SECONDS - start ))
print -u2 -- "$(date '+%F %T') claude exit $rc after ${elapsed}s"

if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc, ${elapsed}s), see $OUT: $(head -c 200 "$OUT")"
  exit $rc
fi

if [[ ! -s "$OUT" ]]; then
  notify "nightly review FAILED: claude exited 0 after ${elapsed}s but $OUT is empty"
  exit 1
fi

# Cut by characters, not bytes, so we never send Telegram a broken UTF-8 sequence.
summary=$(<"$OUT")
notify "nightly review done (${elapsed}s): ${summary[1,300]}"
