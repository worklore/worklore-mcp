#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# Secrets for non-interactive runs (launchd cannot use the interactive
# `claude /login` session). File is chmod 600 and holds e.g.
#   export CLAUDE_CODE_OAUTH_TOKEN=...   (from `claude setup-token`)
#   export TG_BOT_TOKEN=...
ENV_FILE="$HOME/.config/nightly-review/env"
[ -r "$ENV_FILE" ] && source "$ENV_FILE"

# Whatever goes wrong, say so on Telegram instead of dying silently.
TRAPEXIT() {
  local rc=$?
  if [ $rc -ne 0 ] && [ -z "${NOTIFIED:-}" ]; then
    "$NOTIFY" "nightly review FAILED (exit $rc), see ~/Library/Logs/nightly-review.err"
  fi
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; NOTIFIED=1; exit 1; }

# -p mode cannot ask for permission, so pre-approve read-only git commands.
claude -p "$PROMPT" --output-format text \
  --allowedTools "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" "Read" "Grep" "Glob" \
  > "$OUT"
rc=$?   # NB: not "status" -- that is a read-only alias of $? in zsh

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc): $(tail -c 300 "$HOME/Library/Logs/nightly-review.err" 2>/dev/null)"
  NOTIFIED=1
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
NOTIFIED=1
