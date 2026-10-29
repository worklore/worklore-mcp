#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

# launchd does not set USER; without it `claude` cannot find its login in the
# keychain ("Not logged in"). The plist sets it too, this is a fallback.
export USER="${USER:-$(id -un)}"

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

# Send a message; if the notifier itself fails, at least leave a trace in the
# launchd stderr log instead of failing silently.
notify() {
  "$NOTIFY" "$1" || print -u2 -- "$(date '+%F %T') notify.sh failed (rc=$?): $1"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing ($REPO)"; exit 1; }

START=$SECONDS
# Prompt via stdin: no multi-line argument parsing, and claude never waits on
# an open stdin.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$ERR"
rc=$?   # NOT `status`: in zsh it is read-only and assigning to it kills the script
DURATION=$(( SECONDS - START ))
print -- "$(date '+%F %T') claude rc=$rc duration=${DURATION}s"

if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc, ${DURATION}s): $(tail -c 300 "$ERR")"
  exit $rc
fi

# Exit 0 is not proof of work: an empty result means nothing was done.
if [[ ! -s "$OUT" ]]; then
  notify "nightly review FAILED: empty output after ${DURATION}s, see $ERR"
  exit 1
fi

notify "nightly review done (${DURATION}s): $(head -c 300 "$OUT")"
