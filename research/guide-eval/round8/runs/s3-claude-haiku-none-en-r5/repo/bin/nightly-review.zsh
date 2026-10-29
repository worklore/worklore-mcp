#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

# launchd does not get the login session's Claude login ("Not logged in"),
# so the token comes from the keychain: `claude setup-token`, then
# `security add-generic-password -s claude-nightly-oauth -a "$USER" -w`.
if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  CLAUDE_CODE_OAUTH_TOKEN=$(security find-generic-password -s claude-nightly-oauth -w 2>/dev/null) || CLAUDE_CODE_OAUTH_TOKEN=""
fi
if [ -z "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
  "$NOTIFY" "nightly review FAILED: no claude-nightly-oauth token in keychain"
  exit 1
fi
export CLAUDE_CODE_OAUTH_TOKEN

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# stderr goes to its own file: launchd's err log is the only place it lands otherwise.
claude -p "$PROMPT" --output-format text > "$OUT" 2> "$ERR"
claude_rc=$?

# A zero exit with no output is still a failure: nothing to summarize.
if [ $claude_rc -ne 0 ] || [ ! -s "$OUT" ]; then
  code=$claude_rc
  [ $code -eq 0 ] && code=1
  reason=$(head -c 200 "$ERR")
  [ -n "$reason" ] || reason="no output from claude"
  "$NOTIFY" "nightly review FAILED (exit $code): $reason -- see $ERR"
  exit $code
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
