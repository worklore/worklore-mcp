#!/usr/bin/env bash
# usage: run.sh <s1|s3|s7|s8|s10|s11> <agent> <arm> [rep]
# arms (English task, as round 8's en arms):
#   none     the task alone
#   story    the task + "a colleague's note" + the worklore story            (= round 8's example-en)
#   ticket   the task + the same "colleague's note" line + tickets/<s>.md:   the story's facts as a plain ticket
#            comment, without the reproduction contract (see tickets/CHECK.md)
# agents: claude-haiku codex-sol-low (references, same harnesses as round 8)
#         claude-opus, agy-oss  frontier and Antigravity GPT-OSS references on the new stories (as round 8's lanes)
#         agy-flash-low  Gemini 3.8 Flash in Antigravity, as round 8 (added for the story screen, screen.md)
#         codex-oss      GPT-OSS 120B in Codex CLI through OpenRouter
#         vibe-devstral  Devstral 2 in Mistral Vibe CLI through OpenRouter
#         kimi-k31       Kimi K3.1 Pro in Kimi Code (optional lane, ticket arm only)
# The agent works in a fresh neutral dir /tmp/h-XXXXXX; graders, stories and other runs live elsewhere.
set -u
D="$(cd "$(dirname "$0")" && pwd)"
S=$1; A=$2; ARM=$3; REP=${4:-1}
declare -A FIX=([n1]=n1-vibekeychain [n3]=n3-s3deploy [n4]=n4-codexsandbox [n6]=n6-hedera [n7]=n7-pollar [n9]=n9-effect4 [n10]=n10-prisma [s1]=s1-hr [s3]=s3-launchd [s7]=s7-oauth [s8]=s8-cache [s10]=s10-keystroke [s11]=s11-secondwrite)
case $ARM in none|story|ticket) ;; *) echo "unknown arm $ARM"; exit 2;; esac
ID="$S-$A-$ARM-r$REP"; R=$D/runs/$ID; rm -rf "$R"; mkdir -p "$R"
W=$(mktemp -d /tmp/h-XXXXXX); echo "$W" > "$R/workdir"
cp -R "$D/fixtures/${FIX[$S]}/." "$W/"
# n10 needs a PostgreSQL during the run (controls/n10/README.md). Each run gets its own database, so parallel lanes
# don't share one; graders/grade_n10.py derives the same name from the run id and drops it after grading.
if [ "$S" = n10 ]; then
  NDB="n10_$(printf %s "$ID" | tr -c 'a-z0-9' '_')"; PGB=/opt/homebrew/opt/postgresql@17/bin
  LC_ALL=C "$PGB/dropdb" -h localhost -p 5435 -U postgres --if-exists --force "$NDB" >/dev/null 2>&1
  LC_ALL=C "$PGB/createdb" -h localhost -p 5435 -U postgres "$NDB" || echo "$ID: could not create $NDB (is the n10 PostgreSQL running?)" >&2
  sed -i "s#localhost:5435/n10\"#localhost:5435/$NDB\"#" "$W/.env"
fi
cd "$W" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD > "$R/base_commit"
{ cat "$D/prompts/$S.task"
  case $ARM in
    story)  cat "$D/prompts/example.prefix" "$D/stories/$S.md";;
    ticket) cat "$D/prompts/example.prefix" "$D/tickets/$S.md"; echo;;
  esac
  cat "$D/prompts/common.suffix"; } > "$R/prompt.txt"
P="$(cat "$R/prompt.txt")"
E=(env -u AWS_PROFILE -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_SESSION_TOKEN -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY -u PLAUSIBLE_API_KEY -u DATAFORSEO_PASSWORD -u DATAFORSEO_LOGIN -u ANTHROPIC_API_KEY -u OPENROUTER_API_KEY AWS_SHARED_CREDENTIALS_FILE=/dev/null AWS_CONFIG_FILE=/dev/null EVAL_NO_SECRETS=1)
T=1200
start=$(date +%s)
claude_run() { cd "$W" && timeout $T "${E[@]}" claude -p "$P" --model "$1" --dangerously-skip-permissions \
      --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands \
      --setting-sources project,local --settings '{"disableAllHooks":true}' \
      --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
codex_run() { cd "$W" && timeout $T "${E[@]}" codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
      -m "$1" -c model_reasoning_effort="\"$2\"" -C "$W" --json -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
agy_run() { cd "$W" && timeout $T "${E[@]}" ~/.local/bin/agy --model "$1" --dangerously-skip-permissions --add-dir "$W" \
      --disable-slash-commands --output-format stream-json -p "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
# The two OpenRouter lanes (new in round 11). Like Kimi in round 8, the agent has a real shell and its output leaves the
# machine, so it runs under open-sandbox.sb (no reading or writing the real home, no launchctl, security or osascript),
# with the env allowlist of ../sandbox/env.sh plus OPENROUTER_API_KEY, an empty scratch HOME, and its own scratch config
# dir (CODEX_HOME / VIBE_HOME) holding harness/<lane>.toml. Network stays open, as in every other lane.
or_run() { # or_run <codex|vibe>
  local REAL="$HOME" SH CH; SH=$(mktemp -d /tmp/khome-XXXXXX); CH=$(mktemp -d /tmp/ahome-XXXXXX)
  ( cd "$W" && . "$D/../sandbox/env.sh" && export HOME="$SH" SANDBOX_CLI=openrouter
    if [ "$1" = codex ]; then
      cp "$D/harness/codex-oss.toml" "$CH/config.toml"
      sandbox_exec sandbox-exec -D HOME="$REAL" -f "$D/open-sandbox.sb" env CODEX_HOME="$CH" timeout $T \
        codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json -o "$CH/final.txt" "$P" \
        < /dev/null > "$R/agent.log" 2> "$R/agent.err"
    else
      cp "$D/harness/vibe-devstral.toml" "$CH/config.toml"
      # MISTRAL_API_KEY=unused: without any Mistral key in the env, Vibe looks in the macOS Keychain (blocked here) and stops.
      # --max-price caps a runaway run at $1.50; --time-limit makes Vibe write its export before the outer timeout.
      sandbox_exec sandbox-exec -D HOME="$REAL" -f "$D/open-sandbox.sb" env VIBE_HOME="$CH" MISTRAL_API_KEY=unused timeout $((T+60)) \
        "$REAL/.local/bin/vibe" -p "$P" --model devstral --auto-approve --trust --output streaming --output-dir "$CH/vibe-out" \
        --max-price 1.5 --time-limit $T < /dev/null > "$R/agent.log" 2> "$R/agent.err"
    fi )
  # The sandbox denies writes under the real home, where the run folder is, so both CLIs write their final message /
  # export into the scratch dir and it is copied out here (the redirections above are opened outside the sandbox).
  local rc=$?
  [ -f "$CH/final.txt" ] && cp "$CH/final.txt" "$R/final.txt"
  [ -d "$CH/vibe-out" ] && cp -R "$CH/vibe-out" "$R/vibe"
  chmod -R u+w "$SH" "$CH" 2>/dev/null; rm -rf "$SH" "$CH"; return $rc; }
kimi_run() { local REAL="$HOME" SH SK; SH=$(mktemp -d /tmp/khome-XXXXXX); SK=$(mktemp -d /tmp/noskills-XXXXXX)
  ( cd "$W" && . "$D/../sandbox/env.sh" && export HOME="$SH" && sandbox_exec sandbox-exec -D HOME="$REAL" -f "$D/kimi-sandbox.sb" \
      env KIMI_CODE_HOME="$REAL/.kimi-code" KIMI_CODE_NO_AUTO_UPDATE=1 timeout $T "$REAL/.kimi-code/bin/kimi" -m "$1" -p "$P" \
      --output-format stream-json --skills-dir "$SK" < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  local rc=$?; rm -rf "$SH" "$SK"; return $rc; }
case $A in
  claude-opus)    claude_run claude-opus-5-5;;
  claude-haiku)   claude_run claude-haiku-5-5;;
  codex-sol-low)  codex_run gpt-6-sol low;;
  agy-flash-low)  agy_run gemini-3.8-flash-low;;
  agy-oss)        agy_run gpt-oss-120b-medium;;
  codex-oss)      or_run codex;;
  vibe-devstral)  or_run vibe;;
  kimi-k31)       kimi_run kimi-code/k3.1-pro;;
  *) echo "unknown agent $A"; exit 2;;
esac
rc=$?
end=$(date +%s)
cd "$W" && git add -A >/dev/null 2>&1 && git diff --cached "$(cat $R/base_commit)" > "$R/diff.patch"; git reset -q
cp -a "$W" "$R/repo"; cd /; rm -rf "$W"
# The OpenRouter key is in the agent's environment in the Vibe lane: scrub it from everything the run left before
# anything else reads the folder. The value is read from the environment and never printed; only the count is kept.
key_hits=0
if [ -n "${OPENROUTER_API_KEY:-}" ]; then
  key_hits=$(python3 - "$R" <<'EOF'
import os, sys
k = os.environ["OPENROUTER_API_KEY"].encode(); n = 0
for root, _, files in os.walk(sys.argv[1]):
    for f in files:
        p = os.path.join(root, f)
        if os.path.islink(p): continue
        try: b = open(p, "rb").read()
        except OSError: continue
        if k in b:
            n += b.count(k); open(p, "wb").write(b.replace(k, b"[REDACTED-OPENROUTER-KEY]"))
print(n)
EOF
)
fi
# A run that died on a usage limit, a provider error or an outage is not a result: mark it so the lane redoes it later.
limit=false
L="$R/agent.log"; X="$R/agent.err"
if grep -v rate_limit_info "$X" "$L" 2>/dev/null | grep -qiE "hit your limit|usage limit|limit reached|rate limit exceeded|too many requests|out of credits|resource.?exhausted|insufficient_quota|quota exceeded|\"status\": ?429|status code 429|overloaded_error" \
   && [ $((end-start)) -lt 90 ]; then limit=true; fi
if grep -qE "provider.api_error: You've reached your 5-hour usage limit|exceeded_current_quota_error" "$X" "$L" 2>/dev/null; then limit=true; fi
# Antigravity: a provider outage ("No capacity available for model ...", 503) ends the run with a retryable AGY_ERROR.
if grep -qE '^AGY_ERROR: .*"retryable":true' "$X" 2>/dev/null; then limit=true; fi
# OpenRouter: Codex ends a failed turn with "turn.failed" and the HTTP status; Vibe's export names the outcome.
# Only for the two OpenRouter lanes (an eval task about API keys puts these words in other logs too).
# 401 (bad key) and 402 (no credits) stop the whole lane (STOP-<agent>), since every later run would fail the same way.
if grep -qE '"type":"turn.failed".*(unexpected status (401|402|403|408|429|5[0-9][0-9])|upstream returned (429|5[0-9][0-9]))' "$L" 2>/dev/null; then limit=true; fi
if [ -f "$R/vibe/export.json" ] && grep -qE '"outcome": ?"(infrastructure_failure|config_error|provider_error|rate_limited)"' "$R/vibe/export.json"; then limit=true; fi
if [[ $A == codex-oss || $A == vibe-devstral ]] && grep -qiE "unexpected status 40[12]|Invalid API key|Insufficient credits|requires more credits|invalid_api_key|payment required" "$L" "$X" "$R/vibe/export.json" 2>/dev/null; then
  limit=true; echo "$(date '+%F %T') $ID: OpenRouter key rejected or out of credits" >> "$D/STOP-$A"; fi
echo "{\"id\":\"$ID\",\"story\":\"$S\",\"agent\":\"$A\",\"arm\":\"$ARM\",\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start)),\"limit\":$limit,\"key_hits\":$key_hits}" > "$R/meta.json"
python3 "$D/graders/grade_$S.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
echo "$ID rc=$rc wall=$((end-start))s limit=$limit key_hits=$key_hits PASS=$(python3 -c "import json;print(json.load(open('$R/grade.json')).get('PASS'))" 2>/dev/null)"
