#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w) || {
    echo "notify.sh: cannot read tg-bot token from keychain" >&2
    exit 1
  }
fi
CHAT_ID=123456789
resp=$(curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1")
case "$resp" in
  *'"ok":true'*) ;;
  *) echo "notify.sh: telegram API rejected the message: $resp" >&2; exit 1 ;;
esac
