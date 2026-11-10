#!/usr/bin/env bash
# controls/n9/run.sh: grade each n9 control as if an agent had left that repo. Unlike controls/check.sh, the repo is
# installed first (npm ci from the case's package-lock.json), because a run leaves node_modules in R/repo.
# Expected: unmodified False, v3-names False, reference True.
set -u
D="$(cd "$(dirname "$0")/../.." && pwd)"
for CASE in unmodified v3-names reference; do
  R=$(mktemp -d /tmp/ctl-XXXXXX); mkdir -p "$R/repo"
  cp -R "$D/fixtures/n9-effect4/." "$R/repo/"
  ( cd "$R/repo" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD ) > "$R/base_commit"
  cp -R "$D/controls/n9/$CASE/." "$R/repo/"; rm -f "$R/repo/.keep"
  [ -f "$R/repo/package-lock.json" ] && ( cd "$R/repo" && npm ci --silent --no-audit --no-fund >/dev/null 2>&1 )
  : > "$R/agent.log"
  python3 "$D/graders/grade_n9.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
  python3 -c "import json,sys;g=json.load(open(sys.argv[1]));print('n9',sys.argv[2],'PASS=%s'%g.get('PASS'),'effect=%s'%g.get('effect_version'),'tsc_ok=%s'%g.get('tsc_ok'),'tsc_errors=%s'%g.get('tsc_errors'),'tests=%s/5'%g.get('tests_passed'))" "$R/grade.json" "$CASE" || tail -3 "$R/grade.err"
  [ -n "${KEEP:-}" ] && echo "  kept $R" || rm -rf "$R"
done
