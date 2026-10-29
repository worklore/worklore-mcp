#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w)}"
CHAT_ID=123456789
# --fail-with-body: a Telegram API error (HTTP 4xx/5xx) becomes a non-zero exit
# and the response body goes to stderr (the job's log) instead of /dev/null.
resp=$(curl -sS --fail-with-body --max-time 30 -X POST \
  "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1") || {
  rc=$?
  echo "notify.sh: telegram send failed (curl rc=$rc): $resp" >&2
  exit $rc
}
