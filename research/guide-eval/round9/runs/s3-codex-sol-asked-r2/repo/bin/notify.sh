#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
CONFIG="${HOME}/.config/nightly-review/config.toml"

read_config() {
  sed -nE "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*\"?([^\"#[:space:]]+)\"?[[:space:]]*(#.*)?$/\1/p" "$CONFIG" | head -n 1
}

if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(read_config telegram_bot_token)
fi
CHAT_ID=${TG_CHAT_ID:-$(read_config chat_id)}

if [ -z "$TG_BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
  echo "nightly-review: Telegram token or chat ID missing from $CONFIG" >&2
  exit 1
fi

curl -fsS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
