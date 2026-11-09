#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -u

if [ -z "${TG_BOT_TOKEN:-}" ]; then
  if ! TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w 2>/dev/null); then
    echo "notify.sh: cannot read keychain item 'tg-bot'" >&2
    exit 1
  fi
fi
CHAT_ID=123456789
curl -sS --fail -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null || {
  echo "notify.sh: telegram API request failed (exit $?)" >&2
  exit 1
}
