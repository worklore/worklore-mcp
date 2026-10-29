#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w 2>/dev/null)}"
# Empty token (e.g. keychain unreadable under launchd) must be an error, not a silent 404.
if [ -z "$TG_BOT_TOKEN" ]; then
  echo "notify.sh: no Telegram token (keychain item tg-bot not readable)" >&2
  exit 1
fi
CHAT_ID=123456789
# -f: HTTP errors (404, 401...) make curl exit non-zero.
curl -fsS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
