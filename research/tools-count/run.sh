#!/usr/bin/env bash
# One clean headless run.  usage: run.sh <claude|claude-search|codex|gemini> <5..50|GROUPED> <task-id> <rep> [phase]
# Writes runs/<phase>/<model>/<variant>/<task>-r<rep>/ : prompt.txt agent.log agent.err calls.jsonl meta.json row.json
set -u
D="$(cd "$(dirname "$0")" && pwd)"
M=$1; V=$2; T=$3; REP=$4; PHASE=${5:-full}
TIMEOUT=180
R=$D/runs/$PHASE/$M/$V/$T-r$REP
rm -rf "$R"; mkdir -p "$R"

# Server lives at a neutral path with no answer key next to it.
SRV=/tmp/filekit-mcp/server.py
mkdir -p /tmp/filekit-mcp
if ! cmp -s "$D/server.py" "$SRV"; then cp "$D/server.py" "$SRV.tmp.$$" && mv -f "$SRV.tmp.$$" "$SRV"; fi

NEED=$(jq -r --arg t "$T" '.tasks[]|select(.id==$t)|[.expected[].tool]|unique|join(",")' "$D/tasks.json")
TASK=$(jq -r --arg t "$T" '.tasks[]|select(.id==$t)|.prompt' "$D/tasks.json")
FILES=$(jq -r '.files|join(", ")' "$D/tasks.json")
P=$(sed -e "s|{FILES}|$FILES|" "$D/prompts/template.txt"); P=${P//\{TASK\}/$TASK}
printf '%s\n' "$P" > "$R/prompt.txt"

W=$(mktemp -d /tmp/work-XXXXXX)
L=$(mktemp /tmp/fk-XXXXXX); mv "$L" "$L.jsonl"; L="$L.jsonl"
cd "$W" && git init -q
E=(env -u ENABLE_TOOL_SEARCH -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY -u ANTHROPIC_API_KEY -u OPENAI_API_KEY)
start=$(date +%s.%N)
case $M in
  claude|claude-search)
    # claude: --tools "" = no built-ins at all, which also removes ToolSearch, so every MCP schema is loaded upfront
    #         (same as ENABLE_TOOL_SEARCH=false). claude-search: only the ToolSearch built-in, i.e. Claude Code's
    #         default deferred loading of MCP tools; ToolSearch can only find/load MCP tools, it is not a bypass.
    [ $M = claude-search ] && BUILTINS="ToolSearch" || BUILTINS=""
    MCP=$(jq -cn --arg s "$SRV" --arg v "$V" --arg n "$NEED" --arg l "$L" \
      '{mcpServers:{filekit:{command:"python3",args:[$s],env:{TC_VARIANT:$v,TC_NEED:$n,TC_LOG:$l}}}}')
    timeout -k 10 $TIMEOUT "${E[@]}" claude -p "$P" --model claude-opus-5-5 --tools "$BUILTINS" \
      --strict-mcp-config --mcp-config "$MCP" --dangerously-skip-permissions --disable-slash-commands \
      --setting-sources project,local --settings '{"disableAllHooks":true}' --no-session-persistence \
      --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  codex)
    timeout -k 10 $TIMEOUT "${E[@]}" codex exec --ignore-user-config --ignore-rules --skip-git-repo-check -s read-only -C "$W" \
      --disable shell_tool --disable unified_exec --disable apps --disable plugins --disable browser_use --disable browser_use_external \
      --disable computer_use --disable image_generation --disable multi_agent --disable multi_agent_v2 --disable view_image \
      --disable in_app_browser --disable tool_suggest --disable skill_search --disable goals --disable hooks --disable memories \
      --disable sleep_tool --disable workspace_dependencies --disable shell_snapshot \
      -c web_search='"disabled"' -c approval_policy='"never"' \
      -c 'mcp_servers.filekit.command="python3"' -c "mcp_servers.filekit.args=[\"$SRV\"]" \
      -c 'mcp_servers.filekit.default_tools_approval_mode="approve"' \
      -c "mcp_servers.filekit.env={TC_VARIANT=\"$V\",TC_NEED=\"$NEED\",TC_LOG=\"$L\"}" \
      --json -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  gemini)
    # Antigravity: workspace plugin carries the MCP server; a custom main agent keeps only view_file
    # (needed to read lazily-loaded MCP schemas) + the MCP dispatcher. The schema cache dir is global;
    # it is cleared once before the lane starts.
    # (schema cache is shared; all tool schemas are identical across variants, so parallel runs are safe)
    mkdir -p .agents/plugins/filekit .agents/agents
    echo '{"name":"filekit"}' > .agents/plugins/filekit/plugin.json
    jq -n --arg s "$SRV" --arg v "$V" --arg n "$NEED" --arg l "$L" \
      '{mcpServers:{filekit:{command:"python3",args:[$s],env:{TC_VARIANT:$v,TC_NEED:$n,TC_LOG:$l}}}}' > .agents/plugins/filekit/mcp_config.json
    printf '%s\n' '---' 'name: assistant' 'description: General assistant.' 'mainAgent: true' 'inheritMcp: true' 'tools:' '  - view_file' '---' \
      '# assistant' 'You are a helpful assistant. Use the available tools to do what the user asks.' > .agents/agents/assistant.md
    git add -A >/dev/null 2>&1; git -c user.name=u -c user.email=u@local commit -qm init >/dev/null 2>&1
    timeout -k 10 $TIMEOUT "${E[@]}" ~/.local/bin/agy --agent assistant --model gemini-3.1-pro-high --dangerously-skip-permissions \
      --disable-slash-commands --output-format stream-json -p "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
esac
rc=$?
end=$(date +%s.%N)
[ -f "$L" ] && mv "$L" "$R/calls.jsonl" || : > "$R/calls.jsonl"
if [ $M = codex ]; then
  TID=$(grep -m1 -o '"thread_id":"[^"]*"' "$R/agent.log" | cut -d'"' -f4)
  if [ -n "$TID" ]; then f=$(find ~/.codex/sessions -name "*$TID.jsonl" 2>/dev/null | head -1); [ -n "$f" ] && mv "$f" "$R/rollout.jsonl"; fi
fi
cd /; rm -rf "$W"
python3 -c "import json,sys;json.dump({'model':sys.argv[1],'variant':sys.argv[2],'task':sys.argv[3],'rep':int(sys.argv[4]),'phase':sys.argv[5],'exit_code':int(sys.argv[6]),'wall_s':round(float(sys.argv[8])-float(sys.argv[7]),2),'timeout':int(sys.argv[6]) in (124,137)},open(sys.argv[9],'w'))" \
  "$M" "$V" "$T" "$REP" "$PHASE" "$rc" "$start" "$end" "$R/meta.json"
python3 "$D/score.py" "$R" > "$R/row.json" 2> "$R/score.err"
echo "$PHASE $M $V $T r$REP rc=$rc $(jq -c '{status,success,tools_ok,args_ok,wrong:.wrong_calls,n:.n_calls,in:.input_tokens_total,s:.wall_s}' "$R/row.json" 2>/dev/null)"
