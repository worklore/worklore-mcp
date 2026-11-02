#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
# Long-lived token from `claude setup-token` (chmod 600). launchd jobs can't
# use the interactive login stored in the keychain, which is locked at 02:30.
CLAUDE_TOKEN_FILE="$HOME/.config/nightly-review/claude-token"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && [ -r "$CLAUDE_TOKEN_FILE" ]; then
  export CLAUDE_CODE_OAUTH_TOKEN="$(<"$CLAUDE_TOKEN_FILE")"
fi

# Headless mode can't prompt for permissions, so pre-approve read-only git.
claude -p "$PROMPT" --output-format text \
  --allowedTools "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" Read Grep Glob \
  > "$OUT"
rc=$?   # not "status": that is a read-only special parameter in zsh

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc), see $OUT and nightly-review.err"
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
