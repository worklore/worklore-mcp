#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu

if [ -z "${TG_BOT_TOKEN:-}" ]; then
  if ! TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w 2>/dev/null); then
    echo "notify.sh: cannot read tg-bot token from keychain" >&2
    exit 1
  fi
fi

CHAT_ID=123456789

if ! resp=$(curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1"); then
  echo "notify.sh: curl failed to reach Telegram" >&2
  exit 1
fi

case "$resp" in
  *'"ok":true'*) ;;
  *)
    echo "notify.sh: Telegram API error: $resp" >&2
    exit 1
    ;;
esac
