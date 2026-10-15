#!/usr/bin/env bash
# usage: run.sh <s1|s3> <cc|agy> <sonnet|opus> <with|without> <rep>
# Agent works in a fresh neutral dir /tmp/h-XXXXXX; graders and other runs live elsewhere.
set -u
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/3bfdd3c9-cfe2-4fd1-a8b7-ce52b613a3aa/scratchpad/harness-eval
S=$1; H=$2; MD=$3; ARM=$4; REP=$5
declare -A FIX=([s1]=s1-skillscan [s3]=s3-dates)
declare -A STORY=([s1]=2026-09-07-see-what-a-skill-can-do-before-you-run-it-a-stdlib-capabilit [s3]=2026-07-31-author-local-dates-for-a-global-user-content-site)
declare -A CCM=([sonnet]=claude-sonnet-4-6 [opus]=claude-opus-4-6)
declare -A AGM=([sonnet]=claude-sonnet-4-6 [opus]=claude-opus-4-6-thinking)
ID="$S-$H-$MD-$ARM-r$REP"; R=$D/runs/$ID; rm -rf "$R"; mkdir -p "$R"
W=$(mktemp -d /tmp/h-XXXXXX); echo "$W" > "$R/workdir"
cp -R "$D/fixtures/${FIX[$S]}/." "$W/"
cd "$W" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD > "$R/base_commit"
{ cat "$D/prompts/$S.task"
  if [ "$ARM" = with ]; then printf '\nFollow this guide:\n\n'; cat "$D/stories/${STORY[$S]}.md"; fi
  cat "$D/prompts/common.suffix"; } > "$R/prompt.txt"
P="$(cat "$R/prompt.txt")"
E=(env -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY)
T=900
start=$(date +%s)
case $H in
  cc)  cd "$W" && timeout $T "${E[@]}" claude -p "$P" --model ${CCM[$MD]} --dangerously-skip-permissions \
            --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands \
            --setting-sources project,local --settings '{"disableAllHooks":true}' \
            --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  agy) cd "$W" && timeout $T "${E[@]}" ~/.local/bin/agy --model ${AGM[$MD]} --dangerously-skip-permissions --add-dir "$W" \
            --disable-slash-commands --output-format stream-json -p "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
esac
rc=$?
end=$(date +%s)
cd "$W" && git add -A >/dev/null 2>&1 && git diff --cached "$(cat $R/base_commit)" > "$R/diff.patch"; git reset -q
cp -a "$W" "$R/repo"; cd /; rm -rf "$W"
echo "{\"id\":\"$ID\",\"story\":\"$S\",\"harness\":\"$H\",\"model\":\"$MD\",\"arm\":\"$ARM\",\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start))}" > "$R/meta.json"
python3 "$D/graders/grade_$S.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
[ $S = s3 ] && python3 "$D/graders/grade_s3_old.py" "$R" > "$R/grade_old.json" 2>> "$R/grade.err"
echo "$ID rc=$rc wall=$((end-start))s PASS=$(python3 -c "import json;print(json.load(open('$R/grade.json')).get('PASS'))")"
