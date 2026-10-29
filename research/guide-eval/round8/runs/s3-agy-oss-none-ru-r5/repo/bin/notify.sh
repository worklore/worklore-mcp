#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
# Try to get token from keychain; if not found, leave empty
TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w 2>/dev/null || echo "")
CHAT_ID=123456789
if [ -z "$TG_BOT_TOKEN" ]; then
  echo "[notify] No Telegram token found; skipping notification"
  exit 0
fi
curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null