#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  # set -e does not catch a failed $(...) inside `: "${VAR:=$(...)}"`, so check it explicitly.
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w) || { echo "notify: no tg-bot token in keychain" >&2; exit 1; }
fi
CHAT_ID=123456789
# -f: an HTTP error (bad token, bad chat) must fail the script, not print nothing and exit 0.
curl -fsS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
