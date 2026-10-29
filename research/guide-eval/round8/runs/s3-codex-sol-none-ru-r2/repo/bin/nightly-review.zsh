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

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# launchd does not inherit credentials from an interactive shell. A key stored
# under this service name can be used for unattended runs.
if [[ -z ${ANTHROPIC_API_KEY:-} && -z ${CLAUDE_CODE_OAUTH_TOKEN:-} ]]; then
  api_key=$(security find-generic-password -s anthropic-api-key -w 2>/dev/null) && export ANTHROPIC_API_KEY="$api_key"
fi

claude -p "$PROMPT" --output-format text > "$OUT"
claude_exit=$?

if [ "$claude_exit" -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $claude_exit), see $OUT and nightly-review.err"
  exit "$claude_exit"
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
