#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w 2>/dev/null || true)}"
if [ -z "$TG_BOT_TOKEN" ]; then
  echo "notify.sh: no bot token (keychain item tg-bot not readable)" >&2
  exit 1
fi
CHAT_ID=123456789
# -f: an HTTP error (bad token, 404, ...) must fail here instead of being swallowed.
curl -sS -f -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
