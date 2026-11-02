#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
CONFIG="$HOME/.config/nightly-review/config.toml"

toml_get() {  # toml_get key -> value of a simple `key = "value"` / `key = 123` line
  sed -n -E "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*\"?([^\"]*)\"?[[:space:]]*$/\1/p" "$CONFIG" 2>/dev/null | head -n1
}

# Keychain first; it is locked when launchd runs us at night, so fall back to
# the config file kept for exactly that case.
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w 2>/dev/null || true)
fi
if [ -z "$TG_BOT_TOKEN" ]; then
  TG_BOT_TOKEN=$(toml_get telegram_bot_token)
fi
if [ -z "$TG_BOT_TOKEN" ]; then
  echo "notify.sh: no Telegram bot token (keychain locked and none in $CONFIG)" >&2
  exit 1
fi
CHAT_ID=$(toml_get chat_id)
CHAT_ID=${CHAT_ID:-123456789}

curl -sS --fail-with-body -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
