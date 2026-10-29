#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w)}"
[ -n "$TG_BOT_TOKEN" ] || { echo "notify.sh: no bot token" >&2; exit 1; }
CHAT_ID=123456789
# -f: an HTTP error from Telegram (bad token, 404, ...) must fail the script.
curl -sS -f -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
