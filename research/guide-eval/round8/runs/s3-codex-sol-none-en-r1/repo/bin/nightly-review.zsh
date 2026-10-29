#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# launchd does not inherit credentials exported by an interactive shell.
# Use a dedicated Keychain item when the agent needs an API key.
if [[ -z ${ANTHROPIC_API_KEY:-} ]]; then
  api_key=$(security find-generic-password -s nightly-review-anthropic-api-key -w 2>/dev/null) || api_key=
  if [[ -n $api_key ]]; then
    export ANTHROPIC_API_KEY=$api_key
  fi
  unset api_key
fi

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

claude -p "$PROMPT" --output-format text > "$OUT"
review_exit=$?

if (( review_exit != 0 )); then
  "$NOTIFY" "nightly review FAILED (exit $review_exit); see $HOME/Library/Logs/nightly-review.err"
  exit $review_exit
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
