#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w)}"
CHAT_ID=123456789
# --fail-with-body: Telegram API errors (bad token, bad text) become a non-zero
# exit, and the reason goes to stderr instead of /dev/null.
resp=$(curl -sS --fail-with-body -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1") || { echo "notify.sh: $resp" >&2; exit 1; }
