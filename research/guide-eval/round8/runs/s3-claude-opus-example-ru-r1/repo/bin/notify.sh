#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w)}"
CHAT_ID=123456789
# --fail-with-body: an API error (bad token, bad text) is a non-zero exit with
# Telegram's explanation, not a silent success.
if ! resp=$(curl -sS --fail-with-body --max-time 30 \
    -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
    -d chat_id="$CHAT_ID" --data-urlencode text="$1"); then
  echo "notify.sh: telegram send failed: $resp" >&2
  exit 1
fi
