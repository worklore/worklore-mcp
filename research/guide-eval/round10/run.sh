#!/usr/bin/env bash
# usage: run.sh <shell|env> <claude-opus|codex-sol|agy-flash-low> <plain|xray|tool> [rep]
# variant: which added step the s8 story carries (stories/<variant>.md)
# arms: plain = task + note prefix + story + ground rules, no MCP
#       xray  = the same, with the captured check_capability output (xray/<variant>.txt) after the story, no MCP
#       tool  = task + one sentence asking for an x-ray first + note prefix + story + ground rules, proxy.py connected
# The agent works in a fresh dir /tmp/h-XXXXXX, launched through sandbox/env.sh (env -i + allowlist, verify.sh first).
set -u
D="$(cd "$(dirname "$0")" && pwd)"; G="$(cd "$D/.." && pwd)"
. "$G/sandbox/env.sh"
V=$1; A=$2; ARM=$3; REP=${4:-1}
case $V in shell|env) ;; *) echo "unknown variant $V"; exit 2;; esac
case $ARM in plain|xray|tool) ;; *) echo "unknown arm $ARM"; exit 2;; esac
ID="$V-$A-$ARM-r$REP"; R=$D/runs/$ID; rm -rf "$R"; mkdir -p "$R"
W=$(mktemp -d /tmp/h-XXXXXX)
cp -R "$D/fixtures/s8-cache/." "$W/"
cd "$W" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD > "$R/base_commit"
{ cat "$D/prompts/en/s8.task"
  [ "$ARM" = tool ] && { echo; cat "$D/prompts/en/tool.line"; }
  cat "$D/prompts/en/example.prefix" "$D/stories/$V.md"
  [ "$ARM" = xray ] && { echo; echo "worklore's capability x-ray of the note above (check_capability, scanner 0.4.0):"; echo '```'; cat "$D/xray/$V.txt"; echo '```'; }
  cat "$D/prompts/en/common.suffix"; } > "$R/prompt.txt"
P="$(cat "$R/prompt.txt")"
PX="$D/proxy.py"; L="$R/calls.jsonl"; : > "$L"
T=1200
CODEX_BIN=/opt/homebrew/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
start=$(date +%s)
claude_run() { if [ "$ARM" = tool ]; then MCP=$(jq -cn --arg s "$PX" --arg l "$L" '{mcpServers:{worklore:{command:"python3",args:[$s],env:{PH_LOG:$l}}}}'); else MCP='{"mcpServers":{}}'; fi
  cd "$W" && SANDBOX_CLI=claude sandbox_run timeout $T claude -p "$P" --model "$1" --dangerously-skip-permissions \
      --strict-mcp-config --mcp-config "$MCP" --disable-slash-commands \
      --setting-sources project,local --settings '{"disableAllHooks":true}' \
      --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
codex_run() { local M=()
  [ "$ARM" = tool ] && M=(-c 'mcp_servers.worklore.command="python3"' -c "mcp_servers.worklore.args=[\"$PX\"]" \
      -c "mcp_servers.worklore.env={PH_LOG=\"$L\"}" -c 'mcp_servers.worklore.default_tools_approval_mode="approve"')
  cd "$W" && SANDBOX_CLI=codex sandbox_run timeout $T "$CODEX_BIN" exec --ignore-user-config --skip-git-repo-check \
      --dangerously-bypass-approvals-and-sandbox -m "$1" -c model_reasoning_effort="\"$2\"" "${M[@]}" \
      -C "$W" --json -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
agy_run() { cd "$W"
  if [ "$ARM" = tool ]; then mkdir -p .agents/plugins/worklore && echo '.agents/' >> .git/info/exclude
    echo '{"name":"worklore"}' > .agents/plugins/worklore/plugin.json
    jq -n --arg s "$PX" --arg l "$L" '{mcpServers:{worklore:{command:"python3",args:[$s],env:{PH_LOG:$l}}}}' > .agents/plugins/worklore/mcp_config.json; fi
  SANDBOX_CLI=agy sandbox_run timeout $T ~/.local/bin/agy --model "$1" --dangerously-skip-permissions --add-dir "$W" \
      --disable-slash-commands --output-format stream-json -p "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
case $A in
  claude-opus)    claude_run claude-opus-5-5;;
  codex-sol)      codex_run gpt-6-sol medium;;
  agy-flash-low)  agy_run gemini-3.8-flash-low;;
  *) echo "unknown agent $A"; exit 2;;
esac
rc=$?
end=$(date +%s)
cd "$W" && git add -A >/dev/null 2>&1 && git diff --cached "$(cat "$R/base_commit")" > "$R/diff.patch"; git reset -q
rm -rf "$W/.agents"
cp -a "$W" "$R/repo"; rm -rf "$R/repo/.git"; cd /; rm -rf "$W"
limit=false
if grep -v rate_limit_info "$R/agent.err" "$R/agent.log" 2>/dev/null | grep -qiE "hit your limit|usage limit|limit reached|rate limit exceeded|too many requests|out of credits|resource.?exhausted|insufficient_quota|quota exceeded|\"status\": ?429|status code 429|overloaded_error" \
   && [ $((end-start)) -lt 90 ]; then limit=true; fi
if [ "$rc" = 3 ] || grep -qiE "UNAVAILABLE \(code 503\)|No capacity available|experiencing high traffic" "$R/agent.err" 2>/dev/null; then limit=true; fi
[ "$rc" = 97 ] && limit=true
echo "{\"id\":\"$ID\",\"variant\":\"$V\",\"story\":\"s8\",\"agent\":\"$A\",\"arm\":\"$ARM\",\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start)),\"t_start\":$start,\"t_end\":$end,\"limit\":$limit}" > "$R/meta.json"
python3 "$D/graders/grade_s8.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
python3 -I "$D/score.py" "$R" > "$R/score.out" 2>&1
echo "$ID rc=$rc wall=$((end-start))s limit=$limit PASS=$(python3 -c "import json;print(json.load(open('$R/grade.json')).get('PASS'))" 2>/dev/null) $(cat "$R/score.out")"
