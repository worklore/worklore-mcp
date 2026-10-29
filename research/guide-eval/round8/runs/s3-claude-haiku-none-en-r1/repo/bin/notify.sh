#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
# Not `: "${TG_BOT_TOKEN:=$(...)}"`: a failing lookup there leaves the token empty
# and the script still exits 0, so nothing gets sent and nothing is reported.
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w)
fi
CHAT_ID=123456789
# -f: make HTTP errors (bad token, 404, 400) exit non-zero instead of succeeding silently.
curl -fsS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
