#!/usr/bin/env bash
# controls/check.sh <id> <fixture> <case>: grade the fixture with controls/<id>/<case>/ copied over it (an empty case =
# the unmodified fixture), as if an agent had left that repo. Prints the grader's PASS.
set -u
D="$(cd "$(dirname "$0")/.." && pwd)"; ID=$1; FIX=$2; CASE=$3
R=$(mktemp -d /tmp/ctl-XXXXXX); mkdir -p "$R/repo"
cp -R "$D/fixtures/$FIX/." "$R/repo/"
( cd "$R/repo" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD ) > "$R/base_commit"
cp -R "$D/controls/$ID/$CASE/." "$R/repo/" 2>/dev/null; rm -f "$R/repo/.keep"
: > "$R/agent.log"
python3 "$D/graders/grade_$ID.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
echo "$ID $CASE PASS=$(python3 -c "import json;print(json.load(open('$R/grade.json')).get('PASS'))" 2>/dev/null) $(cat "$R/grade.err" | tail -1)"
[ -n "${KEEP:-}" ] && echo "  kept $R" || rm -rf "$R"
