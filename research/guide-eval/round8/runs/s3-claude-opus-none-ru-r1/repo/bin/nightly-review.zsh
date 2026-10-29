#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
LOGDIR="$HOME/Library/Logs"
OUT="$LOGDIR/nightly-review-$(date +%F).md"
ERR="$LOGDIR/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

# launchd does not read ~/.zshrc / ~/.zprofile, so secrets that live there
# (CLAUDE_CODE_OAUTH_TOKEN, TG_BOT_TOKEN) are invisible to this job.
# Keep them in a chmod 600 file instead:
#   export CLAUDE_CODE_OAUTH_TOKEN=...   # from `claude setup-token`
#   export TG_BOT_TOKEN=...
SECRETS="$HOME/.config/nightly-review/env"
[ -r "$SECRETS" ] && source "$SECRETS"

# Send a message; if Telegram delivery itself fails, say so loudly in the
# launchd stderr log and as a local macOS notification, never silently.
notify() {
  if ! "$NOTIFY" "$1"; then
    print -u2 "$(date '+%F %T') notify.sh failed; message was: $1"
    /usr/bin/osascript -e "display notification \"Telegram notify failed, see $LOGDIR/nightly-review.err\" with title \"nightly-review\"" 2>/dev/null
  fi
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { notify "nightly review: repo missing ($REPO)"; exit 1; }

# -p mode cannot answer permission prompts, so pre-approve the read-only
# tools the review needs (git log/show/diff, file reads).
claude -p "$PROMPT" --output-format text \
  --allowedTools "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" Read Grep Glob \
  > "$OUT" 2> "$ERR"
rc=$?   # NB: not "status" -- in zsh that is a read-only alias of $?

if [ $rc -ne 0 ]; then
  cat "$ERR" >&2
  notify "nightly review FAILED (exit $rc): $(head -c 300 "$ERR")"
  exit $rc
fi

notify "nightly review done: $(head -c 300 "$OUT")"
