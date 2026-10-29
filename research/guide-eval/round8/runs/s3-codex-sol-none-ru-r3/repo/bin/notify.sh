#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  if ! TG_BOT_TOKEN=$(/usr/bin/security find-generic-password -s tg-bot -w); then
    echo "notify: Telegram credential unavailable (Keychain item tg-bot)" >&2
    exit 1
  fi
fi
if [ -z "$TG_BOT_TOKEN" ]; then
  echo "notify: Telegram credential is empty" >&2
  exit 1
fi
CHAT_ID=123456789
response=$(/usr/bin/curl --fail --silent --show-error --retry 3 --retry-delay 5 \
  --connect-timeout 10 --max-time 30 -X POST \
  "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1") || exit 1
case "$response" in
  *'"ok":true'*|*'"ok": true'*) ;;
  *) echo "notify: Telegram did not confirm delivery" >&2; exit 1 ;;
esac
