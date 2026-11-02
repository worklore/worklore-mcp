#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
CONFIG_FILE="$HOME/.config/nightly-review/config.toml"

if [ -z "${TG_BOT_TOKEN:-}" ]; then
  if [ -f "$CONFIG_FILE" ]; then
    TG_BOT_TOKEN=$(grep -E '^[[:space:]]*telegram_bot_token[[:space:]]*=' "$CONFIG_FILE" | sed -E 's/^[[:space:]]*telegram_bot_token[[:space:]]*=[[:space:]]*["'"'"']?([^"'"'"']*)["'"'"']?/\1/')
  fi
  if [ -z "${TG_BOT_TOKEN:-}" ]; then
    TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w 2>/dev/null || true)
  fi
fi

if [ -z "${CHAT_ID:-}" ]; then
  if [ -f "$CONFIG_FILE" ]; then
    CHAT_ID=$(grep -E '^[[:space:]]*chat_id[[:space:]]*=' "$CONFIG_FILE" | sed -E 's/^[[:space:]]*chat_id[[:space:]]*=[[:space:]]*["'"'"']?([^"'"'"']*)["'"'"']?/\1/')
  fi
  : "${CHAT_ID:=123456789}"
fi
curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
