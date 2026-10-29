#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
LOG_DIR="$HOME/Library/Logs"
OUT="$LOG_DIR/nightly-review-$(date +%F).md"
ERR="$LOG_DIR/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

report_failure() {
  local message="$1"
  print -u2 -- "$message"
  "$NOTIFY" "$message" || print -u2 -- "nightly review: notification failed"
}

if [[ ! -d "$REPO" ]]; then
  report_failure "nightly review FAILED: repo missing: $REPO"
  exit 1
fi

# launchd does not inherit credentials from an interactive shell.
# Store an Anthropic API key in the login Keychain under this service name.
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  ANTHROPIC_API_KEY=$(/usr/bin/security find-generic-password -s anthropic-api-key -w 2>/dev/null) || ANTHROPIC_API_KEY=""
  export ANTHROPIC_API_KEY
fi
if [[ -z "$ANTHROPIC_API_KEY" ]]; then
  report_failure "nightly review FAILED: Anthropic API key unavailable (Keychain service anthropic-api-key)"
  exit 1
fi

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { report_failure "nightly review FAILED: cannot enter $REPO"; exit 1; }
claude -p "$PROMPT" --output-format text > "$OUT" 2> "$ERR"
rc=$?

if (( rc != 0 )); then
  report_failure "nightly review FAILED (exit $rc), see $ERR"
  exit "$rc"
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || {
  print -u2 -- "nightly review: notification failed"
  exit 1
}
