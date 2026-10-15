#!/usr/bin/env bash
# usage: run.sh <claude|codex|agy-pro|agy-flash> <with|without>
set -u
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/3bfdd3c9-cfe2-4fd1-a8b7-ce52b613a3aa/scratchpad/mp-eval
A=$1; ARM=$2; ID="$A-$ARM"; R=$D/runs/$ID; rm -rf "$R"; mkdir -p "$R"
W=$(mktemp -d /tmp/mp-XXXXXX); W=$(cd "$W" && pwd -P); echo "$W" > "$R/workdir"
cp "$D/prompts/client_brief.md" "$W/"
{ cat "$D/prompts/task.txt"
  if [ "$ARM" = with ]; then printf '\nFollow this guide:\n\n'; cat "$D/prompts/story.md"; fi
  cat "$D/prompts/suffix.txt"; } > "$R/prompt.txt"
P="$(cat "$R/prompt.txt")"
E=(env -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY)
T=900; start=$(date +%s)
cd "$W"
case $A in
  claude) timeout $T "${E[@]}" claude -p "$P" --model claude-opus-5-5 --dangerously-skip-permissions \
            --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands \
            --setting-sources project,local --settings '{"disableAllHooks":true}' \
            --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  codex)  timeout $T "${E[@]}" codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
            -m gpt-6-sol -c model_reasoning_effort='"medium"' -C "$W" --json -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  agy-pro|agy-flash) M=gemini-3.1-pro-high; [ $A = agy-flash ] && M=gemini-3.8-flash-high
          timeout $T "${E[@]}" ~/.local/bin/agy --model $M --dangerously-skip-permissions --add-dir "$W" \
            --output-format stream-json -p "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
esac
rc=$?; end=$(date +%s)
mkdir -p "$R/out"; cp -R "$W/." "$R/out/" 2>/dev/null; cd /; rm -rf "$W"
echo "{\"id\":\"$ID\",\"agent\":\"$A\",\"arm\":\"$ARM\",\"exit_code\":$rc,\"wall_s\":$((end-start))}" > "$R/meta.json"
echo "$ID rc=$rc wall=$((end-start))s files: $(ls "$R/out" | tr '\n' ' ')"
