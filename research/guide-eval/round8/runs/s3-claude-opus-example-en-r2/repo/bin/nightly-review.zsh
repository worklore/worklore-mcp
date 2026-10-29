#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# Every message also goes to stderr (the launchd .err log), so a broken
# notifier can't make a run invisible.
say() {
  print -r -- "$(date '+%F %T') $1" >&2
  "$NOTIFY" "$1" || print -r -- "$(date '+%F %T') notify.sh failed (rc=$?)" >&2
}

START=$SECONDS
say_end() { print -r -- "$(date '+%F %T') run took $(( SECONDS - START ))s" >&2; }

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { say "nightly review FAILED: repo $REPO missing"; say_end; exit 1; }

# Prompt goes in via stdin: no multi-line argv, and claude never waits on an open stdin.
# NB: never assign to `status` in zsh, it is read-only and kills the script.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?

if (( rc != 0 )); then
  say "nightly review FAILED (exit $rc), see $OUT and ~/Library/Logs/nightly-review.err"
  say_end
  exit $rc
fi

# Exit 0 is not proof of work: require actual output.
if [[ ! -s "$OUT" ]]; then
  say "nightly review FAILED: claude exited 0 but $OUT is empty"
  say_end
  exit 1
fi

say "nightly review done: $(head -c 300 "$OUT")"
say_end
