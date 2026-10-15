#!/usr/bin/env bash
# One run: an agent checks ./SKILL.md with worklore's hosted check_capability (anonymous, text input).
# usage: run.sh <claude|codex|gemini> <skill-name> <rep> [phase: before|after-file|after-url]
# Writes runs/<agent>/<skill>-r<rep>/ : agent.log agent.err meta.json
set -u
D=/Users/valentinakoniukhova/projects/worklore/research/2026-10-14-paste-hash
A=$1; S=$2; REP=$3; PH=${4:-before}; TIMEOUT=300
R=$D/runs/$PH/$A/$S-r$REP; rm -rf "$R"; mkdir -p "$R"
PX=$D/proxy.py; L=$R/calls.jsonl
PROMPT='Check the skill in ./SKILL.md with the worklore check_capability tool before I install it. Reply with the tier and the sha256 it returned.'
# after-url: the reader knows where the skill came from, as people installing a public skill usually do
[ $PH = after-url ] && PROMPT="Check the skill in ./SKILL.md with the worklore check_capability tool before I install it. I downloaded it from $(jq -r --arg s "$S" '.[$s]' "$D/urls.json"). Reply with the tier and the sha256 it returned."
W=$(mktemp -d /tmp/ph-XXXXXX); cp "$D/skills/$S.md" "$W/SKILL.md"; cd "$W" && git init -q
E=(env -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY -u ANTHROPIC_API_KEY -u OPENAI_API_KEY)
start=$(date +%s.%N)
case $A in
  claude)
    MCP=$(jq -cn --arg s "$PX" --arg l "$L" '{mcpServers:{worklore:{command:"python3",args:[$s],env:{PH_LOG:$l}}}}')
    timeout -k 10 $TIMEOUT "${E[@]}" claude -p "$PROMPT" --model claude-opus-5-5 --tools Read \
      --strict-mcp-config --mcp-config "$MCP" --dangerously-skip-permissions --disable-slash-commands \
      --setting-sources project,local --settings '{"disableAllHooks":true}' --no-session-persistence \
      --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  codex)
    timeout -k 10 $TIMEOUT "${E[@]}" codex exec --ignore-user-config --ignore-rules --skip-git-repo-check -s read-only -C "$W" \
      --disable apps --disable plugins --disable browser_use --disable browser_use_external --disable computer_use \
      --disable image_generation --disable multi_agent --disable multi_agent_v2 --disable memories --disable hooks \
      -c web_search='"disabled"' -c approval_policy='"never"' \
      -c 'mcp_servers.worklore.command="python3"' -c "mcp_servers.worklore.args=[\"$PX\"]" -c "mcp_servers.worklore.env={PH_LOG=\"$L\"}" -c 'mcp_servers.worklore.default_tools_approval_mode="approve"' \
      --json -o "$R/final.txt" "$PROMPT" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  gemini)
    mkdir -p .agents/plugins/worklore .agents/agents
    echo '{"name":"worklore"}' > .agents/plugins/worklore/plugin.json
    jq -n --arg s "$PX" --arg l "$L" '{mcpServers:{worklore:{command:"python3",args:[$s],env:{PH_LOG:$l}}}}' > .agents/plugins/worklore/mcp_config.json
    printf '%s\n' '---' 'name: assistant' 'description: General assistant.' 'mainAgent: true' 'inheritMcp: true' 'tools:' '  - view_file' '---' \
      '# assistant' 'You are a helpful assistant. Use the available tools to do what the user asks.' > .agents/agents/assistant.md
    git add -A >/dev/null 2>&1; git -c user.name=u -c user.email=u@local commit -qm init >/dev/null 2>&1
    timeout -k 10 $TIMEOUT "${E[@]}" ~/.local/bin/agy --agent assistant --model gemini-3.8-flash-high --dangerously-skip-permissions \
      --disable-slash-commands --output-format stream-json -p "$PROMPT" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
esac
rc=$?; end=$(date +%s.%N)
if [ $A = codex ]; then
  TID=$(grep -m1 -o '"thread_id":"[^"]*"' "$R/agent.log" | cut -d'"' -f4)
  [ -n "$TID" ] && { f=$(find ~/.codex/sessions -name "*$TID.jsonl" 2>/dev/null | head -1); [ -n "$f" ] && mv "$f" "$R/rollout.jsonl"; }
fi
cd /; rm -rf "$W"
jq -n --arg a "$A" --arg s "$S" --argjson rep "$REP" --argjson rc "$rc" --arg st "$start" --arg en "$end" \
  --arg ph "$PH" '{agent:$a,skill:$s,rep:$rep,phase:$ph,exit_code:$rc,wall_s:(($en|tonumber)-($st|tonumber)|.*100|round/100)}' > "$R/meta.json"
python3 "$D/score.py" "$R"
