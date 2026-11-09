#!/usr/bin/env bash
# usage: fresh/run.sh <codex-sol|codex-sol-low> <fresh-en|fresh-ru> [rep]
set -u
F="$(cd "$(dirname "$0")" && pwd)"; D="$(dirname "$F")"
A=$1; ARM=$2; REP=${3:-1}; S=s1
case $ARM in fresh-en) TL=en; CUE="Intervals.icu updated its workout export format in October 2026.";;
             fresh-ru) TL=ru; CUE="Intervals.icu обновил формат экспорта тренировок в октябре 2026.";;
             *) echo "unknown arm $ARM"; exit 2;; esac
ID="$S-$A-$ARM-r$REP"; R=$F/runs/$ID; rm -rf "$R"; mkdir -p "$R"
W=$(mktemp -d /tmp/h-XXXXXX); echo "$W" > "$R/workdir"
cp -R "$D/fixtures/s1-hr/." "$W/"
cd "$W" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD > "$R/base_commit"
# the cue goes right after the task sentence, before the ground rules
python3 - "$D/prompts/$TL/s1.task" "$CUE" "$D/prompts/$TL/common.suffix" > "$R/prompt.txt" <<'PY'
import sys
task=open(sys.argv[1]).read().rstrip('\n'); cue=sys.argv[2]; suf=open(sys.argv[3]).read()
print(task+' '+cue+'\n'+suf, end='')
PY
P="$(cat "$R/prompt.txt")"
E=(env -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY -u PLAUSIBLE_API_KEY -u DATAFORSEO_PASSWORD -u DATAFORSEO_LOGIN -u ANTHROPIC_API_KEY EVAL_NO_SECRETS=1)
T=1200; start=$(date +%s)
codex_run() { cd "$W" && timeout $T "${E[@]}" codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
      -m "$1" -c model_reasoning_effort="\"$2\"" -C "$W" --json -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err"; }
case $A in codex-sol) codex_run gpt-6-sol medium;; codex-sol-low) codex_run gpt-6-sol low;; *) echo "unknown agent $A"; exit 2;; esac
rc=$?; end=$(date +%s)
cd "$W" && git add -A >/dev/null 2>&1 && git diff --cached "$(cat $R/base_commit)" > "$R/diff.patch"; git reset -q
cp -a "$W" "$R/repo"; cd /; rm -rf "$W"
limit=false
if grep -v rate_limit_info "$R/agent.err" "$R/agent.log" 2>/dev/null | grep -qiE "hit your limit|usage limit|limit reached|rate limit exceeded|too many requests|out of credits|insufficient_quota|quota exceeded|\"status\": ?429|status code 429|overloaded_error" && [ $((end-start)) -lt 90 ]; then limit=true; fi
echo "{\"id\":\"$ID\",\"story\":\"$S\",\"agent\":\"$A\",\"arm\":\"$ARM\",\"task_lang\":\"$TL\",\"story_lang\":\"none\",\"cue\":true,\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start)),\"limit\":$limit}" > "$R/meta.json"
python3 "$D/graders/grade_s1.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
echo "$ID rc=$rc wall=$((end-start))s limit=$limit PASS=$(python3 -c "import json;print(json.load(open('$R/grade.json')).get('PASS'))" 2>/dev/null) web=$(python3 -c "import json;print(json.load(open('$R/grade.json')).get('web_used'))" 2>/dev/null)"
