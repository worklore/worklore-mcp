#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
if ! TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w 2>/dev/null); then
  echo "notify.sh: could not read tg-bot token from keychain" >&2
  exit 1
fi
CHAT_ID=123456789
curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
