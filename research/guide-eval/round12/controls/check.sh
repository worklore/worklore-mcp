#!/usr/bin/env bash
# controls/check.sh <h|p> <case>: copy round 11's control case over this round's fixture, npm install (as an agent's run
# leaves node_modules), and grade it. Cases: unmodified (FAIL), the fixture installed as-is on the OLD version
# (old-installed: FAIL + WORKS_ON_OLD), and round 11's reference on the current version (h: ref-hiero, p: ref-prisma8: PASS).
set -u
D="$(cd "$(dirname "$0")/.." && pwd)"; S=$1; CASE=$2
declare -A SRC=([h]=n6 [p]=n10)
X=$(mktemp -d /tmp/ctl-XXXXXX); mkdir -p "$X/repo"; cp -R "$D/fixtures/$S/." "$X/repo/"
( cd "$X/repo" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD ) > "$X/base_commit"
case $CASE in
  unmodified) ;;
  old-installed) ( cd "$X/repo" && npm install --no-audit --no-fund > "$X/npm.log" 2>&1 );;
  *) [ "$S" = p ] && rm -rf "$X/repo/prisma" "$X/repo/prisma.config.ts"
     cp -R "$D/../round11/controls/${SRC[$S]}/$CASE/." "$X/repo/"; rm -f "$X/repo/.keep"
     ( cd "$X/repo" && npm install --no-audit --no-fund > "$X/npm.log" 2>&1 );;
esac
[ "$S" = p ] && [ "$CASE" != unmodified ] && ( cd "$X/repo" && npx prisma generate > /dev/null 2>&1 )
: > "$X/agent.log"
python3 "$D/graders/grade_$S.py" "$X" > "$X/grade.json" 2> "$X/grade.err"
echo "$S $CASE $(python3 -c "import json;g=json.load(open('$X/grade.json'));print({k:g.get(k) for k in ('PASS','WORKS_ON_OLD_SDK','WORKS_ON_PRISMA7','hiero_version','hashgraph_version','on_prisma_8','tables_ok','script_ok','infra_error') if k in g})" 2>/dev/null) $(tail -1 "$X/grade.err")"
[ -n "${KEEP:-}" ] && echo "  kept $X" || rm -rf "$X"
