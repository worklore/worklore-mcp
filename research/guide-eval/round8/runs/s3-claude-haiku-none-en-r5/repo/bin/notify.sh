#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w 2>/dev/null) || TG_BOT_TOKEN=""
fi
if [ -z "$TG_BOT_TOKEN" ]; then
  echo "notify.sh: no tg-bot token (TG_BOT_TOKEN unset, keychain lookup failed)" >&2
  exit 1
fi
CHAT_ID=123456789
# -f: non-2xx from Telegram (bad token, bad chat) is an error, not silence.
curl -fsS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
