#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
CONFIG_FILE="${HOME}/.config/nightly-review/config.toml"
if [ -z "${TG_BOT_TOKEN:-}" ] && [ -f "$CONFIG_FILE" ]; then
  TG_BOT_TOKEN=$(awk -F'=' '/^[[:space:]]*telegram_bot_token[[:space:]]*=/ {print $2}' "$CONFIG_FILE" | tr -d ' "' || true)
fi

: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w 2>/dev/null || true)}"
CHAT_ID=123456789
if [ -f "$CONFIG_FILE" ]; then
  cfg_chat_id=$(awk -F'=' '/^[[:space:]]*chat_id[[:space:]]*=/ {print $2}' "$CONFIG_FILE" | tr -d ' "' || true)
  if [ -n "$cfg_chat_id" ]; then
    CHAT_ID="$cfg_chat_id"
  fi
fi
curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
