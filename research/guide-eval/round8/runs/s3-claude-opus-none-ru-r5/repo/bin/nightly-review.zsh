#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

# launchd does not read ~/.zshrc / ~/.zprofile, so secrets exported there are
# invisible to this job. Put them here instead (chmod 600):
#   CLAUDE_CODE_OAUTH_TOKEN=...   # from `claude setup-token`
#   TG_BOT_TOKEN=...              # optional, otherwise read from Keychain
ENV_FILE="$HOME/.config/nightly-review.env"
if [ -r "$ENV_FILE" ]; then
  set -a; source "$ENV_FILE"; set +a
fi

notify() {
  "$NOTIFY" "$1" || print -u2 "notify.sh failed (exit $?) for: $1"
}

# Any unexpected death of the script (zsh error, signal) still sends a note.
# The pid check keeps $(...) subshells, which inherit the trap, from firing it.
zmodload zsh/system
main_pid=$sysparams[pid]
done_ok=0
TRAPEXIT() {
  if [ $done_ok -eq 0 ] && [ $sysparams[pid] -eq $main_pid ]; then
    notify "nightly review: script aborted unexpectedly, see ~/Library/Logs/nightly-review.err"
  fi
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

if ! cd "$REPO"; then
  notify "nightly review: repo missing ($REPO)"
  done_ok=1
  exit 1
fi

# Headless mode cannot ask for permissions, so allow only read-only tools.
claude -p "$PROMPT" --output-format text \
  --allowedTools "Read" "Grep" "Glob" "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" \
  < /dev/null > "$OUT" 2> "$ERR"
rc=$?   # NB: not "status" -- in zsh $status is a read-only alias of $?

# Keep the shared launchd log useful too.
cat "$ERR" >&2

if [ $rc -ne 0 ]; then
  notify "nightly review FAILED (exit $rc): $(tail -c 300 "$ERR")"
  done_ok=1
  exit $rc
fi

notify "nightly review done: $(head -c 300 "$OUT")"
done_ok=1
