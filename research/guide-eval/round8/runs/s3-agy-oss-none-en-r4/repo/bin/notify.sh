#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
# Retrieve token; if not found, just print message
TG_BOT_TOKEN="${TG_BOT_TOKEN:-}" if [ -z "$TG_BOT_TOKEN" ]; then
  echo "Notify: $1"
  exit 0
fi
CHAT_ID=123456789
curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
