#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

notify() {
  # Never let a Telegram outage turn into silent failure: if notify.sh exits
  # non-zero, leave a trace on stderr (which launchd writes to the err log)
  # and propagate the failure as the job's exit code.
  "$NOTIFY" "$1" || { echo "nightly-review: notify.sh failed (exit $?)" >&2; return 1; }
}

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

claude -p "$PROMPT" --output-format text > "$OUT" 2>&1
rc=$?

if [ $rc -ne 0 ]; then
  notify "nightly review FAILED (exit $rc): $(head -c 300 "$OUT")"
  exit $rc
fi

notify "nightly review done: $(head -c 300 "$OUT")"
