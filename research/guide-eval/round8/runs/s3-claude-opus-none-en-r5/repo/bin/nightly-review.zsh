#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# launchd does not source ~/.zshrc, so whatever auth the interactive shell has
# is not available here. Use a long-lived token from `claude setup-token`,
# stored once with:
#   security add-generic-password -a "$USER" -s claude-code-oauth -w '<token>'
if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
  CLAUDE_CODE_OAUTH_TOKEN=$(security find-generic-password -s claude-code-oauth -w 2>/dev/null) \
    && export CLAUDE_CODE_OAUTH_TOKEN
fi

# Any unexpected exit before the final notification still sends a failure note.
notified=0
TRAPEXIT() {
  local rc=$?
  if (( ! notified )); then
    "$NOTIFY" "nightly review FAILED unexpectedly (exit $rc), see ~/Library/Logs/nightly-review.err"
  fi
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

if ! cd "$REPO"; then
  notified=1
  "$NOTIFY" "nightly review: repo missing"
  exit 1
fi

# Headless mode cannot answer permission prompts: pre-approve read-only tools
# so the agent can actually look at the commits.
claude -p "$PROMPT" --output-format text \
  --allowedTools "Read" "Grep" "Glob" "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" \
  > "$OUT"
rc=$?   # NB: not "status" — that is a read-only special parameter in zsh

if (( rc != 0 )); then
  notified=1
  "$NOTIFY" "nightly review FAILED (exit $rc), see ~/Library/Logs/nightly-review.err"
  exit $rc
fi

notified=1
"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
