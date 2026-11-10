#!/usr/bin/env bash
# controls/n10/check-n10.sh <case>: copy the fixture, lay the case over it, install from the case's lockfile (a real run
# leaves node_modules in the repo), generate the Prisma 7 client when there is a schema.prisma, then grade.
#   unmodified    the fixture as given: FAIL
#   ref-prisma8   Prisma 8 rc.33 set up with `prisma orm init --yes`, contract + emit + db init: PASS
#   prisma7       Prisma 7.10.1 (prisma, @prisma/client, @prisma/adapter-pg), migrate dev: FAIL, WORKS_ON_PRISMA7
# Needs the n10 PostgreSQL on localhost:5435 (README.md).
set -u
D="$(cd "$(dirname "$0")/../.." && pwd)"; CASE=$1
R=$(mktemp -d /tmp/ctl-XXXXXX); mkdir -p "$R/repo"
cp -R "$D/fixtures/n10-prisma/." "$R/repo/"
( cd "$R/repo" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD ) > "$R/base_commit"
cp -R "$D/controls/n10/$CASE/." "$R/repo/"; rm -f "$R/repo/.keep"
if [ -f "$R/repo/package-lock.json" ]; then ( cd "$R/repo" && npm ci --no-audit --no-fund > "$R/npm.log" 2>&1 ); fi
if [ -f "$R/repo/prisma/schema.prisma" ]; then ( cd "$R/repo" && npx --no-install prisma generate >> "$R/npm.log" 2>&1 ); fi
: > "$R/agent.log"
python3 "$D/graders/grade_n10.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
echo "n10 $CASE $(python3 -c "import json;g=json.load(open('$R/grade.json'));print('PASS=%s WORKS_ON_PRISMA7=%s prisma=%s orm_postgres=%s client=%s db=%s tables=%s script=%s tsc=%s'%(g['PASS'],g['WORKS_ON_PRISMA7'],g.get('prisma_version'),g.get('orm_postgres_version'),g.get('prisma_client_version'),g.get('db_source'),g.get('tables_ok'),g.get('script_ok'),g.get('tsc_ok')))" 2>/dev/null) $(tail -1 "$R/grade.err")"
[ -n "${KEEP:-}" ] && echo "  kept $R" || rm -rf "$R"
