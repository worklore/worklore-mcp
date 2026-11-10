#!/usr/bin/env bash
# controls/n7/run.sh: grade each n7 control like controls/check.sh, but run `npm ci` after copying a case that has a
# lockfile (the agent's repo would have node_modules; the controls don't keep them). Prints PASS and the per-trap keys.
set -u
D="$(cd "$(dirname "$0")/../.." && pwd)"; export PATH=/opt/homebrew/opt/node@24/bin:$PATH
for CASE in unmodified solution trap-base-url trap-balance; do
  R=$(mktemp -d /tmp/ctl-XXXXXX); mkdir -p "$R/repo"; cp -R "$D/fixtures/n7-pollar/." "$R/repo/"
  ( cd "$R/repo" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD ) > "$R/base_commit"
  cp -R "$D/controls/n7/$CASE/." "$R/repo/"; rm -f "$R/repo/.keep"; : > "$R/agent.log"
  [ "$CASE" != unmodified ] && ( cd "$R/repo" && npm ci --no-audit --no-fund --silent >/dev/null 2>&1 )
  python3 "$D/graders/grade_n7.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
  python3 -c "import json,sys;g=json.load(open(sys.argv[1]));print(sys.argv[2],'PASS=%s'%g.get('PASS'),'versions=%s tsc=%s base_url=%s balances=%s kyc=%s trustline=%s ramp=%s'%tuple(g.get(k) for k in ('versions_ok','tsc_ok','trap_base_url_ok','trap_balance_ok','kyc_ok','trustline_ok','ramp_ok')))" "$R/grade.json" "$CASE" || tail -3 "$R/grade.err"
  [ -n "${KEEP:-}" ] && echo "  kept $R" || rm -rf "$R"
done
