#!/bin/bash
# usage: notify.sh "message"  — sends a Telegram message to me.
# Token: $TG_BOT_TOKEN, else the login keychain, else ~/.config/nightly-review/config.toml
# (the keychain is locked at 02:30 on that box, so the file is the fallback).
set -eu
CONFIG="$HOME/.config/nightly-review/config.toml"
CHAT_ID=123456789

if [ -z "${TG_BOT_TOKEN:-}" ]; then
  TG_BOT_TOKEN=$(security find-generic-password -s tg-bot -w 2>/dev/null) || TG_BOT_TOKEN=
fi
if [ -z "$TG_BOT_TOKEN" ] && [ -r "$CONFIG" ]; then
  TG_BOT_TOKEN=$(sed -n 's/^[[:space:]]*telegram_bot_token[[:space:]]*=[[:space:]]*"\(.*\)".*/\1/p' "$CONFIG")
  cfg_chat=$(sed -n 's/^[[:space:]]*chat_id[[:space:]]*=[[:space:]]*\([0-9-]*\).*/\1/p' "$CONFIG")
  [ -n "$cfg_chat" ] && CHAT_ID=$cfg_chat
fi
if [ -z "$TG_BOT_TOKEN" ]; then
  echo "notify.sh: no Telegram token (env, keychain and $CONFIG all empty)" >&2
  exit 1
fi

curl -sS -f -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
  -d chat_id="$CHAT_ID" --data-urlencode text="$1" > /dev/null
