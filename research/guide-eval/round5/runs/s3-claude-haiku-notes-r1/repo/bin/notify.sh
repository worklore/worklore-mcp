#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w) ||
    { echo "notify.sh: keychain lookup for tg-bot failed" >&2; exit 1; }
fi
[ -n "$TG_BOT_TOKEN" ] || { echo "notify.sh: empty tg-bot token" >&2; exit 1; }
CHAT_ID=123456789
# -f: a rejected request (bad token, 404, 401) must exit non-zero, not pass silently
curl -sS -f -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
