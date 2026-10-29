#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  # Fails at night if the login keychain is locked; say so instead of
  # silently continuing with an empty token.
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w) || {
    echo "notify.sh: TG_BOT_TOKEN unset and keychain lookup failed" >&2; exit 1; }
fi
CHAT_ID=123456789
# --fail-with-body: non-zero exit on HTTP 4xx/5xx (bad token, bad chat id);
# Telegram's error JSON is reported on stderr instead of going to /dev/null.
resp=$(curl -sS --fail-with-body -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1") \
  || { echo "notify.sh: Telegram sendMessage failed: $resp" >&2; exit 1; }
