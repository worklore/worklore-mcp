#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w)}"
CHAT_ID=123456789
curl -sS --fail-with-body -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null || { echo "notify.sh: Telegram send failed" >&2; exit 1; }
