#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

# launchd gives us no locale; needed so the summary is truncated on
# character (not byte) boundaries and stays valid UTF-8 for Telegram.
export LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

notify() {
  "$NOTIFY" "$1" || print -u2 "nightly review: notify.sh failed (exit $?)"
}

# launchd does not read ~/.zshrc, so claude has no credentials here.
# Long-lived token from `claude setup-token`, stored once with:
#   security add-generic-password -s claude-nightly-token -a "$USER" -w '<token>'
if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
  CLAUDE_CODE_OAUTH_TOKEN=$(security find-generic-password -s claude-nightly-token -w 2>/dev/null) || {
    notify "nightly review FAILED: no Claude token in keychain (claude-nightly-token)"
    exit 1
  }
  export CLAUDE_CODE_OAUTH_TOKEN
fi

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

# Headless mode can't ask for permission: pre-approve read-only tools only,
# otherwise every `git log` is denied and the review sees nothing.
claude -p "$PROMPT" --output-format text \
  --allowedTools "Read" "Grep" "Glob" "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" \
  > "$OUT"
rc=$?   # `status` is a read-only special parameter in zsh

if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc), see $OUT and ~/Library/Logs/nightly-review.err"
  exit $rc
fi

summary=$(<"$OUT")
notify "nightly review done: ${summary[1,300]}"
