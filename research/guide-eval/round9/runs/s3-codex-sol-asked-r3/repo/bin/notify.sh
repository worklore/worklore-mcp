#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu

CONFIG="$HOME/.config/nightly-review/config.toml"
CHAT_ID=123456789
if [[ -r "$CONFIG" ]]; then
  configured_chat_id=$(sed -nE 's/^[[:space:]]*chat_id[[:space:]]*=[[:space:]]*([0-9]+).*$/\1/p' "$CONFIG" | head -n 1)
  [[ -z "$configured_chat_id" ]] || CHAT_ID="$configured_chat_id"
  if [[ -z "${TG_BOT_TOKEN:-}" ]]; then
    TG_BOT_TOKEN=$(sed -nE 's/^[[:space:]]*telegram_bot_token[[:space:]]*=[[:space:]]*"([^"]+)".*$/\1/p' "$CONFIG" | head -n 1)
  fi
fi

if [[ -z "${TG_BOT_TOKEN:-}" ]]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w) || {
    echo "nightly review: Telegram token unavailable" >&2
    exit 1
  }
fi

curl --fail --silent --show-error -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
