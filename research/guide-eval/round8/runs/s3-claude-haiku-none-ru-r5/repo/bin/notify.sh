#!/bin/bash
# usage: notify.sh "message" — sends a Telegram message to me.
set -eu
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w) || {
    echo "notify.sh: no tg-bot token in keychain (run by launchd?)" >&2
    exit 1
  }
fi
CHAT_ID=123456789
# -f: HTTP errors (bad token, 404, 400) make curl exit non-zero instead of
# being discarded. Without it the script "succeeded" on every failed send.
curl -fsS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
