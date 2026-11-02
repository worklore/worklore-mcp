#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
CONFIG="${HOME}/.config/nightly-review/config.toml"
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  if [ -f "$CONFIG" ]; then
    TG_BOT_TOKEN=$(sed -n 's/^[[:space:]]*telegram_bot_token[[:space:]]*=[[:space:]]*["'\'']\([^"'\'']*\)["'\''].*/\1/p' "$CONFIG")
  fi
  : "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w 2>/dev/null || true)}"
fi

if [ -f "$CONFIG" ]; then
  CONFIG_CHAT_ID=$(sed -n 's/^[[:space:]]*chat_id[[:space:]]*=[[:space:]]*["'\'']\{0,1\}\([^"'\'']*\)["'\'']\{0,1\}[[:space:]]*$/\1/p' "$CONFIG")
fi
CHAT_ID="${CONFIG_CHAT_ID:-123456789}"
curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
