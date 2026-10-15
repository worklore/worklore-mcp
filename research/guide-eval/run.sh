#!/usr/bin/env bash
# usage: run.sh <s1|s2|s3> <claude|codex|agy-pro|agy-flash> <with|without>
set -u
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/3bfdd3c9-cfe2-4fd1-a8b7-ce52b613a3aa/scratchpad/story-eval
S=$1; A=$2; ARM=$3
declare -A FIX=([s1]=s1-skillscan [s2]=s2-mcp [s3]=s3-dates)
declare -A STORY=([s1]=2026-09-07-see-what-a-skill-can-do-before-you-run-it-a-stdlib-capabilit [s2]=2026-09-28-my-tests-passed-because-they-agreed-with-me [s3]=2026-07-31-author-local-dates-for-a-global-user-content-site)
ID="$S-$A-$ARM"; R=$D/runs/$ID; rm -rf "$R"; mkdir -p "$R"
cp -R "$D/fixtures/${FIX[$S]}" "$R/repo"
cd "$R/repo" && git init -q && git add -A && git -c user.name=eval -c user.email=eval@local commit -qm base && git rev-parse HEAD > "$R/base_commit"
{ cat "$D/prompts/$S.task"
  if [ "$ARM" = with ]; then printf '\nFollow this guide:\n\n'; cat "$D/stories/${STORY[$S]}.md"; fi
  cat "$D/prompts/common.suffix"; } > "$R/prompt.txt"
P="$(cat "$R/prompt.txt")"
E=(env -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY)
T=900
start=$(date +%s)
case $A in
  claude) cd "$R/repo" && timeout $T "${E[@]}" claude -p "$P" --model claude-opus-5-5 --dangerously-skip-permissions \
            --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands \
            --setting-sources project,local --settings '{"disableAllHooks":true}' \
            --output-format stream-json --verbose < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  codex)  cd "$R/repo" && timeout $T "${E[@]}" codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
            -m gpt-6-sol -c model_reasoning_effort='"medium"' -C "$R/repo" --json -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
  agy-pro|agy-flash) M=gemini-3.1-pro-high; [ $A = agy-flash ] && M=gemini-3.8-flash-high
          cd "$R/repo" && timeout $T "${E[@]}" ~/.local/bin/agy --model $M --dangerously-skip-permissions --add-dir "$R/repo" \
            --output-format stream-json -p "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err";;
esac
rc=$?
end=$(date +%s)
cd "$R/repo" && git add -A >/dev/null 2>&1 && git diff --cached "$(cat $R/base_commit)" > "$R/diff.patch"; git reset -q
echo "{\"id\":\"$ID\",\"story\":\"$S\",\"agent\":\"$A\",\"arm\":\"$ARM\",\"exit_code\":$rc,\"wall_s\":$((end-start))}" > "$R/meta.json"
python3 "$D/graders/grade_$S.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
echo "$ID rc=$rc wall=$((end-start))s"; cat "$R/grade.json"
