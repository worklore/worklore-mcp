#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
# Token lookup: $TG_BOT_TOKEN, then the keychain, then
# ~/.config/nightly-review/config.toml (for when the keychain is locked at night).
set -eu
CONF="$HOME/.config/nightly-review/config.toml"
CHAT_ID=123456789

toml_get() {  # toml_get key  -> value of a simple `key = "value"` / `key = 123` line
  [ -r "$CONF" ] || return 0
  sed -n -E "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*\"?([^\"]*)\"?[[:space:]]*\$/\1/p" "$CONF" | head -n1
}

if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w 2>/dev/null || true)
fi
if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(toml_get telegram_bot_token)
fi
cfg_chat=$(toml_get chat_id)
CHAT_ID=${cfg_chat:-$CHAT_ID}

if [ -z "${TG_BOT_TOKEN:-}" ]; then
  echo "notify.sh: no Telegram token (env, keychain and $CONF all empty); message was: $1" >&2
  exit 2
fi

if ! curl -sS --fail-with-body -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
     -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null; then
  echo "notify.sh: Telegram send failed; message was: $1" >&2
  exit 3
fi
