#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w) || {
    echo "notify.sh: cannot read tg-bot token from keychain (locked? no access from launchd?)" >&2
    exit 1
  }
fi
CHAT_ID=123456789
# --fail-with-body: non-2xx from Telegram (bad token, chat, text too long...)
# becomes a non-zero exit; the API's error JSON is copied to stderr.
resp=$(curl -sS --fail-with-body --max-time 30 \
  -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="${1:0:4000}") || {
  rc=$?
  echo "notify.sh: Telegram send failed (curl exit $rc): $resp" >&2
  exit "$rc"
}
