#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
NOTIFY="$HOME/bin/notify.sh"

# Headless auth: a launchd job cannot do the interactive `claude /login` OAuth
# flow (and the OAuth keychain item may be unreachable at night), so
# authenticate with an Anthropic API key kept in the login keychain. Create it
# once by hand:
#   security add-generic-password -s anthropic-api-key -a "$USER" -w '<key>'
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  if KEY=$(security find-generic-password -s anthropic-api-key -w 2>/dev/null); then
    export ANTHROPIC_API_KEY="$KEY"
    unset KEY
  fi
fi

NOTIFIED=0
note() { NOTIFIED=1; "$NOTIFY" "$1"; }

# Safety net: whatever kills this script, the failure must still reach Telegram.
trap 'rc=$?
if [ $rc -ne 0 ] && [ $NOTIFIED -eq 0 ]; then
  "$NOTIFY" "nightly review FAILED unexpectedly (exit $rc), see $OUT"
fi' EXIT

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || { note "nightly review: repo missing"; exit 1; }

if ! command -v claude >/dev/null 2>&1; then
  note "nightly review FAILED: claude not found on PATH"
  exit 127
fi

claude -p "$PROMPT" --output-format text > "$OUT"
rc=$?

if [ $rc -ne 0 ]; then
  note "nightly review FAILED (exit $rc), see $OUT"
  exit $rc
fi

note "nightly review done: $(head -c 300 "$OUT")"
