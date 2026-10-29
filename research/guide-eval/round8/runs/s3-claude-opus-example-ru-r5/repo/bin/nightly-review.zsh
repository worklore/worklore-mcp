#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

# Every notification attempt is logged; a failing notifier must not be silent.
notify() {
  "$NOTIFY" "$1" || print -u2 -- "$(date '+%F %T') notify.sh failed (rc=$?) for: $1"
}

# Last-resort reporter: fires on any exit that did not go through the success path.
DONE=0
START=$SECONDS
trap 'rc=$?; (( DONE )) || notify "nightly review FAILED unexpectedly (exit $rc) after $((SECONDS-START))s, see ~/Library/Logs/nightly-review.err"' EXIT

print -u2 -- "$(date '+%F %T') start (USER=${USER:-unset} HOME=$HOME)"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo $REPO missing"; DONE=1; exit 1; }

# Prompt via stdin: no dependence on multi-line argv, and claude never waits on an open stdin.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$ERR"
rc=$?   # never `status`: it is a read-only zsh builtin, assigning to it kills the script
dur=$((SECONDS - START))
print -u2 -- "$(date '+%F %T') claude exit=$rc duration=${dur}s out_bytes=$(wc -c < "$OUT" | tr -d ' ')"

err=$(<"$ERR")
if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc, ${dur}s): ${err[1,300]}"
  DONE=1
  exit $rc
fi

# Exit 0 is not proof of work: empty output counts as failure.
if [[ ! -s "$OUT" ]]; then
  notify "nightly review FAILED: claude exited 0 after ${dur}s but produced no output. ${err[1,300]}"
  DONE=1
  exit 1
fi

summary=$(<"$OUT")
notify "nightly review done (${dur}s): ${summary[1,300]}"
DONE=1
