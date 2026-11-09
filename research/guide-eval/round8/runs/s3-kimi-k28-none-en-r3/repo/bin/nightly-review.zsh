#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# Optional job env, e.g. CLAUDE_CODE_OAUTH_TOKEN from `claude setup-token` (see ANSWER.md).
ENV_FILE="$HOME/.config/nightly-review.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

notify() {
  "$NOTIFY" "$1" && return 0
  echo "notify.sh failed — unsent message: $1" >&2
  return 1
}

cd "$REPO" || { notify "nightly review: repo missing"; exit 1; }

claude -p "$PROMPT" --output-format text > "$OUT"
rc=$?

if [ "$rc" -ne 0 ]; then
  notify "nightly review FAILED (exit $rc), see $OUT"
  exit "$rc"
fi

notify "nightly review done: $(head -c 300 "$OUT")"
