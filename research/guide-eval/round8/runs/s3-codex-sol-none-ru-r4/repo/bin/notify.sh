#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
if [[ -z "${TG_BOT_TOKEN:-}" ]]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w) || {
    echo "notify: could not read Telegram token from Keychain" >&2
    exit 1
  }
fi
if [[ -z "$TG_BOT_TOKEN" ]]; then
  echo "notify: Telegram token is empty" >&2
  exit 1
fi
CHAT_ID=123456789
curl --fail --silent --show-error --max-time 30 -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
