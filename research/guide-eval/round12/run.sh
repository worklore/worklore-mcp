#!/usr/bin/env bash
# usage: run.sh <h|p|p8> <en|ru|uk|es> <agent> <none|line|story> [rep]
# tasks: h = update the Hedera SDK in a project on @hashgraph/sdk 2.70.0 (fixtures/h)
#        p = upgrade Prisma in a project on Prisma 7.6.0 whose tables already exist (fixtures/p)
#        p8 = the same project, the task names the target: "upgrade Prisma to version 8" (her call 2026-11-16, because
#             prisma@latest is 8.0.0-rc.33 and agents that read the dist-tags chose the stable 7.10.1 on purpose)
# arms:  none   the task alone
#        line   the task alone, with prompts/agents-line.md placed as AGENTS.md and CLAUDE.md in the project
#        story  the task + the colleague's-note prefix (task language) + the private worklore story (English)
# agents: claude-haiku     Claude Code, Haiku 5.5 (subscription)
#         codex-sol-low    Codex CLI, GPT-6-Sol, effort low (subscription), as rounds 8 and 11
#         kimi-k31         Kimi Code, K3.1 Pro, default effort, under kimi-sandbox.sb (output goes to Moonshot)
#         claude-deepseek  Claude Code with DeepSeek V4.1 Flash through DeepSeek's Anthropic-compatible API, under
#                          open-sandbox.sb with an empty HOME and config dir (output goes to DeepSeek)
set -u
D="$(cd "$(dirname "$0")" && pwd)"
S=$1; L=$2; A=$3; ARM=$4; REP=${5:-1}
case $S in h|p|p8) ;; *) echo "unknown task $S"; exit 2;; esac
case $L in en|ru|uk|es) ;; *) echo "unknown language $L"; exit 2;; esac
case $ARM in none|line|story) ;; *) echo "unknown arm $ARM"; exit 2;; esac
ID="$S-$L-$A-$ARM-r$REP"; R=$D/runs/$ID; rm -rf "$R"; mkdir -p "$R"
W=$(mktemp -d /tmp/h-XXXXXX); echo "$W" > "$R/workdir"
cp -R "$D/fixtures/$S/." "$W/"
[ "$ARM" = line ] && { cp "$D/prompts/agents-line.md" "$W/AGENTS.md"; cp "$D/prompts/agents-line.md" "$W/CLAUDE.md"; }
PGB=/opt/homebrew/opt/postgresql@17/bin
# p: each run gets its own database, a copy of p_template (Prisma 7.6.0 migrations applied, as in a real project), so
# parallel lanes don't share one. graders/grade_p.py derives the same name from the run id and drops it after grading.
if [ "$S" = p ] || [ "$S" = p8 ]; then
  NDB="n10_$(printf %s "$ID" | tr -c 'a-z0-9' '_')"
  LC_ALL=C "$PGB/dropdb" -h localhost -p 5435 -U postgres --if-exists --force "$NDB" >/dev/null 2>&1
  LC_ALL=C "$PGB/createdb" -h localhost -p 5435 -U postgres -T p_template "$NDB" || echo "$ID: could not create $NDB (is PostgreSQL on 5435 running, does p_template exist?)" >&2
  sed -i "s#localhost:5435/n10\"#localhost:5435/$NDB\"#" "$W/.env"
fi
cd "$W" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD > "$R/base_commit"
{ cat "$D/prompts/$L/$S.task"
  [ "$ARM" = story ] && { cat "$D/prompts/$L/example.prefix"; echo; cat "$D/stories/$S.md"; }
  cat "$D/prompts/$L/common.suffix"; } > "$R/prompt.txt"
P="$(cat "$R/prompt.txt")"
E=(env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_SESSION_TOKEN -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY -u PLAUSIBLE_API_KEY -u DATAFORSEO_PASSWORD -u DATAFORSEO_LOGIN -u ANTHROPIC_API_KEY -u OPENROUTER_API_KEY -u DEEPSEEK_API_KEY AWS_SHARED_CREDENTIALS_FILE=/dev/null AWS_CONFIG_FILE=/dev/null EVAL_NO_SECRETS=1)
T=1200
start=$(date +%s)
claude_run() { cd "$W" && timeout $T "${E[@]}" claude -p "$P" --model "$1" --dangerously-skip-permissions \
      --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands \
      --setting-sources project,local --settings '{"disableAllHooks":true}' \
      --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
codex_run() { cd "$W" && timeout $T "${E[@]}" codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
      -m "$1" -c model_reasoning_effort="\"$2\"" -C "$W" --json -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
kimi_run() { local REAL="$HOME" SH SK; SH=$(mktemp -d /tmp/khome-XXXXXX); SK=$(mktemp -d /tmp/noskills-XXXXXX)
  ( cd "$W" && . "$D/../sandbox/env.sh" && export HOME="$SH" && sandbox_exec sandbox-exec -D HOME="$REAL" -f "$D/kimi-sandbox.sb" \
      env KIMI_CODE_HOME="$REAL/.kimi-code" KIMI_CODE_NO_AUTO_UPDATE=1 timeout $T "$REAL/.kimi-code/bin/kimi" -m "$1" -p "$P" \
      --output-format stream-json --skills-dir "$SK" < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  local rc=$?; rm -rf "$SH" "$SK"; return $rc; }
# DeepSeek: the key comes from the lane's environment (lane.sh reads ~/.zshenv's DEEPSEEK_API_KEY) and is handed to
# Claude Code as ANTHROPIC_AUTH_TOKEN, nothing else. Empty HOME and CLAUDE_CONFIG_DIR: no user CLAUDE.md, hooks,
# skills or MCP servers. The real home is unreadable (open-sandbox.sb). The key is scrubbed from the run folder below.
deepseek_run() {
  local REAL="$HOME" SH CH; SH=$(mktemp -d /tmp/khome-XXXXXX); CH=$(mktemp -d /tmp/ccfg-XXXXXX)
  ( cd "$W" && . "$D/../sandbox/env.sh" && export HOME="$SH" && sandbox_exec sandbox-exec -D HOME="$REAL" -f "$D/open-sandbox.sb" \
      env CLAUDE_CONFIG_DIR="$CH" ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic ANTHROPIC_AUTH_TOKEN="$DEEPSEEK_API_KEY" \
      ANTHROPIC_MODEL=deepseek-flash ANTHROPIC_SMALL_FAST_MODEL=deepseek-flash ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-flash \
      ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-flash CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 timeout $T \
      claude -p "$P" --model deepseek-flash --dangerously-skip-permissions \
      --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands \
      --setting-sources project,local --settings '{"disableAllHooks":true}' \
      --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  local rc=$?; chmod -R u+w "$SH" "$CH" 2>/dev/null; rm -rf "$SH" "$CH"; return $rc; }
case $A in
  claude-haiku)    claude_run claude-haiku-5-5;;
  codex-sol-low)   codex_run gpt-6-sol low;;
  kimi-k31)        kimi_run kimi-code/k3.1-pro;;
  claude-deepseek) deepseek_run;;
  *) echo "unknown agent $A"; exit 2;;
esac
rc=$?
end=$(date +%s)
cd "$W" && git add -A >/dev/null 2>&1 && git diff --cached "$(cat $R/base_commit)" > "$R/diff.patch"; git reset -q
# node_modules is huge and the grader reinstalls from the lockfile when it is missing; keep it for grading only.
cp -a "$W" "$R/repo"; cd /; rm -rf "$W"
key_hits=0
if [ "$A" = claude-deepseek ] && [ -n "${DEEPSEEK_API_KEY:-}" ]; then
  key_hits=$(python3 - "$R" <<'EOF'
import os, sys
k = os.environ["DEEPSEEK_API_KEY"].encode(); n = 0
for root, _, files in os.walk(sys.argv[1]):
    for f in files:
        p = os.path.join(root, f)
        if os.path.islink(p): continue
        try: b = open(p, "rb").read()
        except OSError: continue
        if k in b:
            n += b.count(k); open(p, "wb").write(b.replace(k, b"[REDACTED-DEEPSEEK-KEY]"))
print(n)
EOF
)
fi
limit=false
LG="$R/agent.log"; X="$R/agent.err"
if grep -v rate_limit_info "$X" "$LG" 2>/dev/null | grep -qiE "hit your limit|usage limit|limit reached|rate limit exceeded|too many requests|out of credits|resource.?exhausted|insufficient_quota|quota exceeded|\"status\": ?429|status code 429|overloaded_error" \
   && [ $((end-start)) -lt 90 ]; then limit=true; fi
if grep -qE "provider.api_error: You've reached your 5-hour usage limit|exceeded_current_quota_error" "$X" "$LG" 2>/dev/null; then limit=true; fi
# DeepSeek: 402 = balance gone, 401 = key rejected. Every later run would fail the same way: stop the lane.
if [ "$A" = claude-deepseek ] && grep -qiE "Insufficient Balance|API Error: 40[12]|authentication_error|invalid api key" "$LG" "$X" 2>/dev/null; then
  limit=true; echo "$(date '+%F %T') $ID: DeepSeek key rejected or balance gone" >> "$D/STOP-$A"; fi
echo "{\"id\":\"$ID\",\"task\":\"$S\",\"lang\":\"$L\",\"agent\":\"$A\",\"arm\":\"$ARM\",\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start)),\"limit\":$limit,\"key_hits\":$key_hits}" > "$R/meta.json"
python3 "$D/graders/grade_$S.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
rm -rf "$R/repo/node_modules"
echo "$ID rc=$rc wall=$((end-start))s limit=$limit key_hits=$key_hits PASS=$(python3 -c "import json;print(json.load(open('$R/grade.json')).get('PASS'))" 2>/dev/null)"
