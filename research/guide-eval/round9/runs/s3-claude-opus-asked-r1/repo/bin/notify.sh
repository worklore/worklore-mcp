#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
set -eu
# At 02:30 the login keychain may be locked, so `security` fails and set -e
# kills us silently. Fall back to the config file (chmod 600).
CONFIG="$HOME/.config/nightly-review/config.toml"
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w 2>/dev/null) ||
    TG_BOT_TOKEN=$(sed -n 's/^telegram_bot_token *= *"\(.*\)"/\1/p' "$CONFIG" 2>/dev/null)
fi
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  echo "notify.sh: no Telegram token (keychain locked and $CONFIG unreadable)" >&2
  exit 1
fi
CHAT_ID=123456789
curl -sS -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
