#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# launchd does not read ~/.zshrc / ~/.zprofile, so anything exported there
# (API keys, tokens) is missing here. Put secrets the job needs in this file
# (chmod 600), e.g.:
#   export CLAUDE_CODE_OAUTH_TOKEN=...   # from `claude setup-token`
#   export TG_BOT_TOKEN=...
ENV_FILE="$HOME/.config/nightly-review.env"
[ -r "$ENV_FILE" ] && source "$ENV_FILE"

log() { print -r -- "$(date '+%F %T') $*" >&2; }

notify() {
  "$NOTIFY" "$1" || log "notify.sh failed (exit $?) for message: $1"
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
Start with a three-line summary I can read on my phone.
Then, for each commit: one line on what it changes and whether anything looks
risky (migrations, auth, payments, deleted tests).
Do not modify any file."

cd "$REPO" || { log "repo missing: $REPO"; notify "nightly review: repo missing"; exit 1; }

log "starting review since $SINCE"
# Headless mode cannot ask for permission, so pre-approve read-only tools only.
claude -p "$PROMPT" --output-format text \
  --allowedTools "Read" "Grep" "Glob" \
    "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" \
  > "$OUT" 2>> "$OUT.err"
# NB: `status` is a read-only special parameter in zsh (same as $?);
# assigning to it aborts the script, so use another name.
rc=$?

if [ $rc -ne 0 ]; then
  err=$(tail -c 300 "$OUT.err" 2>/dev/null)
  log "claude failed (exit $rc): $err"
  notify "nightly review FAILED (exit $rc): $err
see $OUT.err"
  exit $rc
fi

log "done"
# Telegram messages max out at 4096 chars.
notify "nightly review done:
$(head -c 3500 "$OUT")"
