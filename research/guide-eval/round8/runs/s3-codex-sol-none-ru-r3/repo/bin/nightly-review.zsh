#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u
umask 077

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

report_failure() {
  print -u2 -- "$1"
  "$NOTIFY" "$1" || print -u2 -- "nightly review: failed to send Telegram notification"
}

# launchd does not inherit credentials exported in an interactive shell.
# A dedicated Keychain item gives this unattended job an explicit credential.
if [[ -z "${ANTHROPIC_API_KEY:-}" && -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]]; then
  if api_key=$(/usr/bin/security find-generic-password -s nightly-review-anthropic-api-key -w 2>/dev/null) && [[ -n "$api_key" ]]; then
    export ANTHROPIC_API_KEY="$api_key"
  else
    report_failure "nightly review FAILED: Claude credential unavailable (Keychain item nightly-review-anthropic-api-key)"
    exit 1
  fi
fi

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { report_failure "nightly review FAILED: repo missing ($REPO)"; exit 1; }

if claude -p "$PROMPT" --output-format text > "$OUT"; then
  if [[ ! -s "$OUT" ]]; then
    report_failure "nightly review FAILED: Claude returned empty output, see $OUT"
    exit 1
  fi
else
  exit_code=$?
  report_failure "nightly review FAILED (exit $exit_code), see $OUT and nightly-review.err"
  exit "$exit_code"
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")" || {
  print -u2 -- "nightly review: failed to send Telegram notification"
  exit 1
}
