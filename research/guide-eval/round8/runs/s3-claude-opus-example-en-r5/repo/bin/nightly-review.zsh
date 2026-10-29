#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

# Never let a broken notifier be silent: log its failure to stderr (launchd log).
notify() { "$NOTIFY" "$1" || print -u2 -- "$(date '+%F %T') notify.sh failed (rc=$?): $1"; }

START=$SECONDS
print -u2 -- "$(date '+%F %T') nightly-review start (USER=${USER:-unset})"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

# Prompt via stdin: no multi-line argument parsing, and claude never waits on an open stdin.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$ERR"
rc=$?            # NOT `status`: it is a read-only special parameter in zsh
DUR=$(( SECONDS - START ))
cat "$ERR" >&2
print -u2 -- "$(date '+%F %T') claude exit=$rc duration=${DUR}s output_bytes=$(wc -c < "$OUT" | tr -d ' ')"

if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc, ${DUR}s): $(tail -c 300 "$ERR")"
  exit $rc
fi

# Exit 0 is not proof of work: an empty summary is a failure too.
if [[ ! -s "$OUT" ]]; then
  notify "nightly review FAILED: claude exited 0 but produced no output (${DUR}s): $(tail -c 300 "$ERR")"
  exit 1
fi

notify "nightly review done (${DUR}s): $(head -c 300 "$OUT")"
