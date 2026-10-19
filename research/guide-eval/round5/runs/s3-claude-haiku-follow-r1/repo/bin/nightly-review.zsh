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

# Failure reporter. Called first on every failure path, so nothing can
# run before it and kill it. Never assign to `status` in zsh (read-only).
fail() {
  print -r -- "$(date '+%F %T') FAILED: $1"
  "$NOTIFY" "nightly review FAILED: $1"
  exit 1
}

start=$SECONDS
print -r -- "$(date '+%F %T') start since=$SINCE"

cd "$REPO" || fail "repo missing at $REPO"

# Prompt goes via stdin, not as an argument: no multi-line argv parsing
# under launchd, and stdin is never left open for the CLI to wait on.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
rc=$?
elapsed=$(( SECONDS - start ))
print -r -- "$(date '+%F %T') claude exit=$rc duration=${elapsed}s out=$OUT"

if (( rc != 0 )); then
  fail "claude exit $rc after ${elapsed}s, see $OUT"
fi

# Exit 0 with nothing written is still a failure.
if [[ ! -s "$OUT" ]]; then
  fail "empty output after ${elapsed}s, see $OUT"
fi

"$NOTIFY" "nightly review done (${elapsed}s): $(head -c 300 "$OUT")"
