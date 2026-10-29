#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"

# launchd does not read ~/.zshrc / ~/.zprofile, so anything the job needs
# (CLAUDE_CODE_OAUTH_TOKEN from `claude setup-token`, optionally TG_BOT_TOKEN)
# lives in a private env file. Keep it chmod 600.
ENV_FILE="$HOME/.config/nightly-review/env"
if [[ -r "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
fi

notify() {
  "$NOTIFY" "$1" || print -u2 "$(date '+%F %T') notify.sh failed (exit $?): $1"
}

# Whatever happens below, never exit silently: if the script dies before
# reporting, send a failure note from the EXIT trap.
reported=0
trap '(( reported )) || notify "nightly review died unexpectedly (exit $?), see ~/Library/Logs/nightly-review.err"' EXIT

fail() {
  reported=1
  notify "nightly review FAILED: $1"
  exit 1
}

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || fail "repo $REPO missing"
command -v claude >/dev/null || fail "claude not found in PATH ($PATH)"

claude -p "$PROMPT" --output-format text > "$OUT" 2> "$ERR"
# NB: `status` is a read-only special parameter in zsh (same as $?),
# assigning to it kills the script — use another name.
rc=$?
cat "$ERR" >&2

if (( rc != 0 )); then
  fail "claude exit $rc: $(head -c 300 "$ERR")"
fi
if [[ ! -s "$OUT" ]]; then
  fail "claude returned empty output, see $ERR"
fi

reported=1
notify "nightly review done: $(head -c 300 "$OUT")"
