#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w) || {
    printf '%s\n' 'notify: cannot read Telegram token from Keychain' >&2
    exit 1
  }
fi
if [ -z "$TG_BOT_TOKEN" ]; then
  printf '%s\n' 'notify: Telegram token is empty' >&2
  exit 1
fi
CHAT_ID=123456789
curl -fSs -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
