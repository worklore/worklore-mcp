#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$OUT.err"
NOTIFY="$HOME/bin/notify.sh"

# Every message also goes to stderr (-> nightly-review.err), so a failing
# notifier never leaves us with total silence.
notify() {
  print -r -- "$(date '+%F %T') $1" >&2
  "$NOTIFY" "$1" || print -r -- "$(date '+%F %T') notify.sh failed (exit $?)" >&2
}

START=$SECONDS
print -r -- "$(date '+%F %T') start (USER=${USER:-unset})" >&2

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing ($REPO)"; exit 1; }

# Prompt via stdin: no multi-line argv parsing and no hanging on an open stdin.
# NB: never assign to `status` in zsh — it is a read-only alias of $?.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$ERR"
rc=$?
dur=$(( SECONDS - START ))

if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc, ${dur}s): $(tail -c 300 "$ERR")"
  exit $rc
fi

# Exit 0 is not proof of work: require non-empty output.
if [[ ! -s "$OUT" ]]; then
  notify "nightly review FAILED: exit 0 but empty output after ${dur}s, see $ERR"
  exit 2
fi

notify "nightly review done (${dur}s): $(head -c 300 "$OUT")"
