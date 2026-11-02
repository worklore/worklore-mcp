#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
CONFIG="$HOME/.config/nightly-review/config.toml"
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(sed -nE 's/^[[:space:]]*telegram_bot_token[[:space:]]*=[[:space:]]*"([^"]+)"[[:space:]]*(#.*)?$/\1/p' "$CONFIG" | head -n 1)
fi
if [ -z "${TG_CHAT_ID:-}" ]; then
  TG_CHAT_ID=$(sed -nE 's/^[[:space:]]*chat_id[[:space:]]*=[[:space:]]*([0-9]+)[[:space:]]*(#.*)?$/\1/p' "$CONFIG" | head -n 1)
fi
: "${TG_BOT_TOKEN:?missing Telegram bot token}"
: "${TG_CHAT_ID:?missing Telegram chat ID}"
curl --fail --silent --show-error -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d "chat_id=$TG_CHAT_ID" --data-urlencode "text=$1" > /dev/null
