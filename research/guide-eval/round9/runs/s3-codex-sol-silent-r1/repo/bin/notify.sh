#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu

CONFIG="$HOME/.config/nightly-review/config.toml"

# The unattended job cannot rely on an unlocked login keychain.
if [ -z "${TG_BOT_TOKEN:-}" ] && [ -r "$CONFIG" ]; then
  TG_BOT_TOKEN=$(sed -n 's/^[[:space:]]*telegram_bot_token[[:space:]]*=[[:space:]]*"\([^"]*\)"[[:space:]]*$/\1/p' "$CONFIG" | head -n 1)
fi
if [ -z "${TG_CHAT_ID:-}" ] && [ -r "$CONFIG" ]; then
  TG_CHAT_ID=$(sed -n 's/^[[:space:]]*chat_id[[:space:]]*=[[:space:]]*\([0-9][0-9]*\)[[:space:]]*$/\1/p' "$CONFIG" | head -n 1)
fi

if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w) || {
    echo "nightly review: no Telegram token in config or accessible keychain" >&2
    exit 1
  }
fi
: "${TG_CHAT_ID:?nightly review: chat_id missing from config and TG_CHAT_ID is unset}"

curl --fail --silent --show-error --max-time 20 -X POST \
  "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d "chat_id=$TG_CHAT_ID" --data-urlencode "text=$1" > /dev/null
