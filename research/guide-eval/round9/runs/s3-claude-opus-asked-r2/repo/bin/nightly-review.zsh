#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"
CONF_DIR="$HOME/.config/nightly-review"

# Under launchd at 02:30 the login keychain may be locked, so `claude` cannot
# read its interactive login. A long-lived token from `claude setup-token`,
# stored in a chmod 600 file, works without the keychain.
if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" && -r "$CONF_DIR/claude-token" ]]; then
  export CLAUDE_CODE_OAUTH_TOKEN="$(<"$CONF_DIR/claude-token")"
fi

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

start=$SECONDS
# Prompt on stdin: no stdin wait under launchd, no multi-line argv surprises.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2>> "$OUT.err"
# NB: never `status=$?` in zsh — `status` is read-only and assigning kills the script.
rc=$?
elapsed=$(( SECONDS - start ))
print -r -- "$(date '+%F %T') claude exit=$rc after ${elapsed}s" >&2

if (( rc != 0 )); then
  "$NOTIFY" "nightly review FAILED (exit $rc, ${elapsed}s): $(tail -c 200 "$OUT.err" 2>/dev/null)"
  exit $rc
fi

if [[ ! -s "$OUT" ]]; then
  "$NOTIFY" "nightly review FAILED: claude exited 0 after ${elapsed}s but wrote nothing"
  exit 1
fi

"$NOTIFY" "nightly review done (${elapsed}s): $(head -c 300 "$OUT")"
