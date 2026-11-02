#!/usr/bin/env bash
# usage: run.sh <s1|s3|s7|s8|s10|s11> <claude-opus|codex-sol|agy-flash-low> <asked|silent> [rep]
# arms: asked  = the round-8 English task + one sentence pointing at the worklore MCP server + ground rules
#       silent = the same task and ground rules, the server connected but not mentioned
# The agent works in a fresh dir /tmp/h-XXXXXX, launched through sandbox/env.sh (env -i + allowlist,
# verify.sh first). The worklore MCP server is proxy.py; it logs every call to the run's calls.jsonl.
set -u
D="$(cd "$(dirname "$0")" && pwd)"; G="$(cd "$D/.." && pwd)"
. "$G/sandbox/env.sh"
S=$1; A=$2; ARM=$3; REP=${4:-1}
declare -A FIX=([s1]=s1-hr [s3]=s3-launchd [s7]=s7-oauth [s8]=s8-cache [s10]=s10-keystroke [s11]=s11-secondwrite)
case $ARM in asked|silent) ;; *) echo "unknown arm $ARM"; exit 2;; esac
ID="$S-$A-$ARM-r$REP"; R=$D/runs/$ID; rm -rf "$R"; mkdir -p "$R"
W=$(mktemp -d /tmp/h-XXXXXX)
cp -R "$D/fixtures/${FIX[$S]}/." "$W/"
cd "$W" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD > "$R/base_commit"
{ cat "$D/prompts/en/$S.task"
  [ "$ARM" = asked ] && { echo; cat "$D/prompts/en/asked.line"; }
  cat "$D/prompts/en/common.suffix"; } > "$R/prompt.txt"
P="$(cat "$R/prompt.txt")"
PX="$D/proxy.py"; L="$R/calls.jsonl"; : > "$L"
T=1200
# Codex's npm wrapper needs node, and homebrew's node is linked against a simdjson that was upgraded
# from under it (dyld: libsimdjson.29.dylib not loaded); the native binary inside the package runs fine.
CODEX_BIN=/opt/homebrew/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/bin/codex
start=$(date +%s)
claude_run() { MCP=$(jq -cn --arg s "$PX" --arg l "$L" '{mcpServers:{worklore:{command:"python3",args:[$s],env:{PH_LOG:$l}}}}')
  cd "$W" && SANDBOX_CLI=claude sandbox_run timeout $T claude -p "$P" --model "$1" --dangerously-skip-permissions \
      --strict-mcp-config --mcp-config "$MCP" --disable-slash-commands \
      --setting-sources project,local --settings '{"disableAllHooks":true}' \
      --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
codex_run() { cd "$W" && SANDBOX_CLI=codex sandbox_run timeout $T "$CODEX_BIN" exec --ignore-user-config --skip-git-repo-check \
      --dangerously-bypass-approvals-and-sandbox -m "$1" -c model_reasoning_effort="\"$2\"" \
      -c 'mcp_servers.worklore.command="python3"' -c "mcp_servers.worklore.args=[\"$PX\"]" \
      -c "mcp_servers.worklore.env={PH_LOG=\"$L\"}" -c 'mcp_servers.worklore.default_tools_approval_mode="approve"' \
      -C "$W" --json -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
# Antigravity: a project-level plugin carries the MCP server; the DEFAULT agent sees its tools and keeps its own
# read/write/run tools (smoke-tested 2026-11-01). A custom .agents/agents/*.md with no `tools:` line gets only
# view_file + call_mcp_tool + manage_task, and `call_mcp_tool` is not a listable tool name, so no custom agent here.
agy_run() { cd "$W" && mkdir -p .agents/plugins/worklore && echo '.agents/' >> .git/info/exclude
  echo '{"name":"worklore"}' > .agents/plugins/worklore/plugin.json
  jq -n --arg s "$PX" --arg l "$L" '{mcpServers:{worklore:{command:"python3",args:[$s],env:{PH_LOG:$l}}}}' > .agents/plugins/worklore/mcp_config.json
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
# A run that died on a usage limit is not a result: mark it so the lane can redo it later.
limit=false
if grep -v rate_limit_info "$R/agent.err" "$R/agent.log" 2>/dev/null | grep -qiE "hit your limit|usage limit|limit reached|rate limit exceeded|too many requests|out of credits|resource.?exhausted|insufficient_quota|quota exceeded|\"status\": ?429|status code 429|overloaded_error" \
   && [ $((end-start)) -lt 90 ]; then limit=true; fi
# A provider outage mid-run (Antigravity 503 "no capacity", agy exit 3) is not a result either, whatever the wall time.
if [ "$rc" = 3 ] || grep -qiE "UNAVAILABLE \(code 503\)|No capacity available|experiencing high traffic" "$R/agent.err" 2>/dev/null; then limit=true; fi
# The sandbox refused to launch (verify.sh failed): not a result either.
[ "$rc" = 97 ] && limit=true
echo "{\"id\":\"$ID\",\"story\":\"$S\",\"fixture\":\"${FIX[$S]}\",\"agent\":\"$A\",\"arm\":\"$ARM\",\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start)),\"t_start\":$start,\"t_end\":$end,\"limit\":$limit}" > "$R/meta.json"
python3 "$D/graders/grade_$S.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
python3 -I "$D/score.py" "$R" > "$R/score.out" 2>&1
echo "$ID rc=$rc wall=$((end-start))s limit=$limit PASS=$(python3 -c "import json;print(json.load(open('$R/grade.json')).get('PASS'))" 2>/dev/null) $(cat "$R/score.out")"
