#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# launchd does not source ~/.zshrc and gives no login session, so claude
# sees no credentials. Use a long-lived token from `claude setup-token`,
# stored once with:
#   security add-generic-password -a "$USER" -s claude-code-oauth -w '<token>'
if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
  CLAUDE_CODE_OAUTH_TOKEN=$(security find-generic-password -s claude-code-oauth -w 2>/dev/null) \
    && export CLAUDE_CODE_OAUTH_TOKEN
fi

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# In -p mode nothing can be approved interactively: allow read-only git and
# file tools explicitly, everything else (edits, other commands) stays denied.
claude -p "$PROMPT" --output-format text \
  --allowedTools "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" Read Grep Glob \
  > "$OUT" 2>&1
# NB: `status` is a read-only special parameter in zsh (same as $?), hence rc.
rc=$?

if (( rc != 0 )); then
  "$NOTIFY" "nightly review FAILED (exit $rc): $(head -c 300 "$OUT")"
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
