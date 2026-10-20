#!/usr/bin/env bash
# usage: run.sh <s1> <claude|codex|agy-argon|agy-flash> <with|without> [rep]
# The agent works in a fresh neutral dir /tmp/h-XXXXXX; graders, stories and other runs live elsewhere.
set -u
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/45aea092-d156-403e-85fa-11e392426b83/scratchpad/guide-eval-r6
S=$1; A=$2; ARM=$3; REP=${4:-1}
declare -A FIX=([s1]=s1-skillscan [s4]=s4-hearback-schema)
ID="$S-$A-$ARM-r$REP"; R=$D/runs/$ID; rm -rf "$R"; mkdir -p "$R"
W=$(mktemp -d /tmp/h-XXXXXX); echo "$W" > "$R/workdir"
cp -R "$D/fixtures/${FIX[$S]}/." "$W/"
cd "$W" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD > "$R/base_commit"
{ cat "$D/prompts/$S.task"
  if [ "$ARM" = with ]; then printf '\nFollow this guide:\n\n'; cat "$D/stories/$S.md"; fi
  cat "$D/prompts/common.suffix"; } > "$R/prompt.txt"
P="$(cat "$R/prompt.txt")"
E=(env -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY -u PLAUSIBLE_API_KEY -u DATAFORSEO_PASSWORD -u DATAFORSEO_LOGIN)
T=900
start=$(date +%s)
case $A in
  claude) cd "$W" && timeout $T "${E[@]}" claude -p "$P" --model claude-opus-5-5 --dangerously-skip-permissions \
            --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands \
            --setting-sources project,local --settings '{"disableAllHooks":true}' \
            --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  codex)  cd "$W" && timeout $T "${E[@]}" codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
            -m gpt-6-sol -c model_reasoning_effort='"medium"' -C "$W" --json -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  agy-argon|agy-flash) M=gemini-4-argon-high; [ $A = agy-flash ] && M=gemini-3.8-flash-high
          cd "$W" && timeout $T "${E[@]}" ~/.local/bin/agy --model $M --dangerously-skip-permissions --add-dir "$W" \
            --disable-slash-commands --output-format stream-json -p "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
esac
rc=$?
end=$(date +%s)
cd "$W" && git add -A >/dev/null 2>&1 && git diff --cached "$(cat $R/base_commit)" > "$R/diff.patch"; git reset -q
cp -a "$W" "$R/repo"; cd /; rm -rf "$W"
echo "{\"id\":\"$ID\",\"story\":\"$S\",\"agent\":\"$A\",\"arm\":\"$ARM\",\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start))}" > "$R/meta.json"
python3 "$D/graders/grade_$S.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
echo "$ID rc=$rc wall=$((end-start))s PASS=$(python3 -c "import json;print(json.load(open('$R/grade.json')).get('PASS'))" 2>/dev/null)"
