#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

# launchd does not source ~/.zshrc, so the interactive login is not visible
# here. Use a long-lived token from `claude setup-token`, stored in the login
# keychain with:
#   security add-generic-password -U -a "$USER" -s claude-oauth-token -w
if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  CLAUDE_CODE_OAUTH_TOKEN=$(security find-generic-password -s claude-oauth-token -w 2>/dev/null) \
    || { "$NOTIFY" "nightly review FAILED: no claude-oauth-token in keychain"; exit 1; }
  export CLAUDE_CODE_OAUTH_TOKEN
fi

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# Headless mode cannot prompt for permissions, so pre-approve read-only git.
claude -p "$PROMPT" --output-format text \
  --allowedTools "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" Read Grep Glob \
  > "$OUT" 2> "$ERR"
# NB: `status` is a read-only special parameter in zsh (same as $?);
# assigning to it aborts the script before any notification is sent.
rc=$?

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc): $(head -c 300 "$ERR")"
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
