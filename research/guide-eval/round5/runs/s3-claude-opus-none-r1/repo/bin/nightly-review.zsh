#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# launchd does not run your login shell, so nothing from ~/.zshrc/.zprofile
# (ANTHROPIC_API_KEY, CLAUDE_CODE_OAUTH_TOKEN, ...) is visible here.
# Put the credentials the job needs in this file (chmod 600), e.g.
#   export CLAUDE_CODE_OAUTH_TOKEN=...   # from `claude setup-token`
#   export TG_BOT_TOKEN=...
ENV_FILE="$HOME/.config/nightly-review/env"
[ -r "$ENV_FILE" ] && source "$ENV_FILE"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# Headless mode can't prompt for permissions, so pre-approve read-only tools.
# Capture stderr too, so a failure note can say what went wrong.
claude -p "$PROMPT" --output-format text \
  --allowedTools "Read" "Grep" "Glob" "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" \
  > "$OUT" 2> "$OUT.err"
# NB: `status` is a read-only special parameter in zsh (alias of $?); use rc.
rc=$?

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc): $(head -c 300 "$OUT.err") — see $OUT.err"
  exit $rc
fi

# The phone summary is at the end of the output, so send the tail.
"$NOTIFY" "nightly review done: $(tail -n 3 "$OUT")"
