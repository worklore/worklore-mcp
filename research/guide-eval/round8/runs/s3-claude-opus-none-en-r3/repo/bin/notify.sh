#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w)}"
CHAT_ID=123456789
# --fail-with-body: a non-2xx reply from Telegram makes curl exit non-zero and
# the error body goes to stderr (the launchd .err log) instead of /dev/null.
curl -sS --fail-with-body -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" >&2
