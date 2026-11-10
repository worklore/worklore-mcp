#!/usr/bin/env bash
# run-vibe.sh "<prompt>" [workdir]: one headless Mistral Vibe run on Devstral 2 through OpenRouter, inside agent.sb.
# The agent gets an empty scratch HOME and VIBE_HOME and only the environment names listed below (env -i), so none of
# my other secrets reach it. OPENROUTER_API_KEY must be set in the calling shell.
set -u
D="$(cd "$(dirname "$0")" && pwd)"
PROMPT=$1; W=${2:-$PWD}
REAL="$HOME"
VIBE="${VIBE:-$REAL/.local/bin/vibe}"
[ -n "${OPENROUTER_API_KEY:-}" ] || { echo "set OPENROUTER_API_KEY first"; exit 1; }
SH=$(mktemp -d /tmp/vhome-XXXXXX); VH=$(mktemp -d /tmp/vibehome-XXXXXX)
cp "$D/vibe/config.toml" "$VH/config.toml"; echo MISTRAL_API_KEY=unused > "$VH/.env"
mkdir -p "$D/logs"
( cd "$W" && env -i PATH="$PATH" TERM="${TERM:-dumb}" LANG="${LANG:-en_US.UTF-8}" HOME="$SH" VIBE_HOME="$VH" \
    OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
    sandbox-exec -D HOME="$REAL" -f "$D/agent.sb" \
    "$VIBE" -p "$PROMPT" --model devstral --auto-approve --trust --output streaming --output-dir "$VH/out" \
      --max-price 1.5 --time-limit 1200 < /dev/null > "$D/logs/last-run.out" 2> "$D/logs/last-run.err" )
rc=$?
[ -d "$VH/out" ] && cp -R "$VH/out" "$D/logs/last-run-export"
chmod -R u+w "$SH" "$VH" 2>/dev/null; rm -rf "$SH" "$VH"
echo "exit $rc"; exit $rc
