#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { "$NOTIFY" "nightly review: repo missing"; exit 1; }

# launchd has no interactive login session: pass a long-lived token
# (made once with `claude setup-token`, stored with
# `security add-generic-password -s claude-oauth -a "$USER" -w <token>`).
if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  CLAUDE_CODE_OAUTH_TOKEN=$(security find-generic-password -s claude-oauth -w 2>/dev/null) \
    && export CLAUDE_CODE_OAUTH_TOKEN
fi

# NB: `status` is read-only in zsh, so use another name.
claude -p "$PROMPT" --output-format text > "$OUT" 2> "$OUT.err"
rc=$?

if [ $rc -ne 0 ]; then
  "$NOTIFY" "nightly review FAILED (exit $rc): $(head -c 200 "$OUT.err")"
  exit $rc
fi

"$NOTIFY" "nightly review done: $(head -c 300 "$OUT")"
