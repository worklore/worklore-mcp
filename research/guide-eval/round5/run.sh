#!/usr/bin/env bash
# usage: run.sh <s1..s6> <agent> <none|follow|example|notes> [rep]
# agents: claude-opus claude-sonnet claude-haiku codex-sol codex-sol-low agy-argon-high agy-argon-low agy-flash-low agy-oss
# The agent works in a fresh neutral dir /tmp/h-XXXXXX; graders, stories and other runs live elsewhere.
set -u
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/45aea092-d156-403e-85fa-11e392426b83/scratchpad/guide-eval-r5
S=$1; A=$2; ARM=$3; REP=${4:-1}
declare -A FIX=([s1]=s1-hr [s2]=s2-posthog [s3]=s3-launchd [s4]=s4-deploy [s5]=s5-soft404 [s6]=s6-mcpcheck)
declare -A NOTE=([s1]=exact-hr-corridors-on-garmin-from-intervals-icu-api-workouts.md
                 [s2]=posthog-session-replay-not-working-in-flutter.md
                 [s3]=two-bugs-made-my-scheduler-perfectly-silent.md
                 [s4]=a-cache-header-tweak-served-my-whole-site-as-octet-stream.md
                 [s5]=soft-404-on-pages-that-load-fine.md
                 [s6]=check-your-mcp-server-in-a-few-minutes.md)
ID="$S-$A-$ARM-r$REP"; R=$D/runs/$ID; rm -rf "$R"; mkdir -p "$R"
W=$(mktemp -d /tmp/h-XXXXXX); echo "$W" > "$R/workdir"
cp -R "$D/fixtures/${FIX[$S]}/." "$W/"
PORT=8765
if [ "$S" = s6 ]; then
  PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
  sed -i "s/8765/$PORT/g" "$W/server.py" "$W/README.md"
fi
echo "$PORT" > "$R/port"
if [ "$ARM" = notes ]; then
  mkdir -p "$W/notes"; cp "$D/stories/$S.md" "$W/notes/${NOTE[$S]}"; cp "$D/decoys/"*.md "$W/notes/"
fi
cd "$W" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD > "$R/base_commit"
{ sed "s/8765/$PORT/g" "$D/prompts/$S.task"
  case $ARM in
    follow)  cat "$D/prompts/follow.prefix"  "$D/stories/$S.md";;
    example) cat "$D/prompts/example.prefix" "$D/stories/$S.md";;
  esac
  cat "$D/prompts/common.suffix"; } > "$R/prompt.txt"
P="$(cat "$R/prompt.txt")"
E=(env -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY -u PLAUSIBLE_API_KEY -u DATAFORSEO_PASSWORD -u DATAFORSEO_LOGIN -u ANTHROPIC_API_KEY EVAL_NO_SECRETS=1)
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
case $A in
  claude-opus)    claude_run claude-opus-5-5;;
  claude-sonnet)  claude_run claude-sonnet-5-5;;
  claude-haiku)   claude_run claude-haiku-5-5;;
  codex-sol)      codex_run gpt-6-sol medium;;
  codex-sol-low)  codex_run gpt-6-sol low;;
  agy-argon-high) agy_run gemini-4-argon-high;;
  agy-argon-low)  agy_run gemini-4-argon-low;;
  agy-flash-low)  agy_run gemini-3.8-flash-low;;
  agy-oss)        agy_run gpt-oss-120b-medium;;
  *) echo "unknown agent $A"; exit 2;;
esac
rc=$?
end=$(date +%s)
# stop anything the agent left listening on the run's port (s6 server)
if [ "$S" = s6 ]; then lsof -ti tcp:"$PORT" 2>/dev/null | xargs -r kill 2>/dev/null; fi
cd "$W" && git add -A >/dev/null 2>&1 && git diff --cached "$(cat $R/base_commit)" > "$R/diff.patch"; git reset -q
cp -a "$W" "$R/repo"; cd /; rm -rf "$W"
echo "{\"id\":\"$ID\",\"story\":\"$S\",\"agent\":\"$A\",\"arm\":\"$ARM\",\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start)),\"port\":$PORT}" > "$R/meta.json"
python3 "$D/graders/grade_$S.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
echo "$ID rc=$rc wall=$((end-start))s PASS=$(python3 -c "import json;print(json.load(open('$R/grade.json')).get('PASS'))" 2>/dev/null)"
