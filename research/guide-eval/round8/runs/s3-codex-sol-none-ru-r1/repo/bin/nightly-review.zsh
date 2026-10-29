#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -eu

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
MESSAGE="nightly review FAILED (unexpected script error); see $HOME/Library/Logs/nightly-review.err"

on_exit() {
  local exit_code=$1
  trap - EXIT
  if ! "$NOTIFY" "$MESSAGE"; then
    print -u2 "nightly review: notification failed (job exit $exit_code)"
    exit 1
  fi
}
trap 'on_exit $?' EXIT

if ! cd "$REPO"; then
  MESSAGE="nightly review FAILED: repo missing: $REPO"
  exit 1
fi

# launchd does not inherit credentials exported by an interactive shell.
# A dedicated API key may be stored in the login Keychain for this job.
if [[ -z ${ANTHROPIC_API_KEY:-} ]]; then
  api_key=$(security find-generic-password -s nightly-review-anthropic-api-key -w 2>/dev/null) || api_key=""
  if [[ -n $api_key ]]; then
    export ANTHROPIC_API_KEY="$api_key"
  fi
  unset api_key
fi

YESTERDAY=$(date -v-1d +%F)
TODAY=$(date +%F)
PROMPT="Review the commits in this repository from $YESTERDAY 00:00 through $TODAY 00:00.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

if claude -p "$PROMPT" --output-format text > "$OUT"; then
  if [[ ! -s $OUT ]]; then
    MESSAGE="nightly review FAILED: Claude returned no summary; see $HOME/Library/Logs/nightly-review.err"
    exit 1
  fi
  MESSAGE="nightly review done: $(head -c 300 "$OUT")"
else
  rc=$?
  MESSAGE="nightly review FAILED (Claude exit $rc); see $HOME/Library/Logs/nightly-review.err"
  exit "$rc"
fi
