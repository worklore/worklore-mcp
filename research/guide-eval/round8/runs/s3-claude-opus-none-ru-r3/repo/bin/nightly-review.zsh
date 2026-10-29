#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# Under launchd nothing from ~/.zshrc is loaded, so pass Claude credentials
# explicitly. Create the token once with `claude setup-token`, then store it:
#   security add-generic-password -U -s claude-nightly-token -a "$USER" -w '<token>'
if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
  if token=$(security find-generic-password -s claude-nightly-token -w 2>/dev/null); then
    export CLAUDE_CODE_OAUTH_TOKEN="$token"
  fi
  unset token
fi

notify() {
  "$NOTIFY" "$1" || print -u2 "$(date '+%F %T') notify.sh failed (exit $?) for: $1"
}

# Any unexpected abort of this script still produces a message.
done_ok=0
trap '(( done_ok )) || notify "nightly review: script aborted unexpectedly, see ~/Library/Logs/nightly-review.err"' EXIT

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

if ! cd "$REPO"; then
  done_ok=1
  notify "nightly review: repo missing ($REPO)"
  exit 1
fi

# In -p mode tools that need permission are denied, so allow read-only git explicitly.
claude -p "$PROMPT" --output-format text \
  --allowedTools "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" Read Grep Glob \
  > "$OUT"
rc=$?   # NB: $status is a read-only alias of $? in zsh; assigning it aborts the script

done_ok=1
if (( rc != 0 )); then
  notify "nightly review FAILED (exit $rc): $(tail -n 3 "$HOME/Library/Logs/nightly-review.err" 2>/dev/null)"
  exit $rc
fi

notify "nightly review done: $(head -c 300 "$OUT")"
