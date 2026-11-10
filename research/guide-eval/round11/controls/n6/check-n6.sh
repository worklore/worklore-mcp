#!/usr/bin/env bash
# controls/n6/check-n6.sh <case>: like controls/check.sh, but runs `npm install` after copying the case over the fixture,
# since every n6 result needs node_modules (an agent's run leaves them in the repo). Prints PASS and WORKS_ON_OLD_SDK.
#   unmodified        the fixture as given: FAIL
#   ref-hiero         reference solution on @hiero-ledger/sdk: PASS
#   old-hashgraph     the same code on @hashgraph/sdk 2.81.0: FAIL, WORKS_ON_OLD_SDK
#   both-imports-old  both packages installed, code imports the old one (as one Gemini 4 Argon run did in the 2026-11-02 screen): FAIL, WORKS_ON_OLD_SDK
set -u
D="$(cd "$(dirname "$0")/../.." && pwd)"; CASE=$1
R=$(mktemp -d /tmp/ctl-XXXXXX); mkdir -p "$R/repo"
cp -R "$D/fixtures/n6-hedera/." "$R/repo/"
( cd "$R/repo" && git init -q && git add -A && git -c user.name=dev -c user.email=dev@local commit -qm base && git rev-parse HEAD ) > "$R/base_commit"
cp -R "$D/controls/n6/$CASE/." "$R/repo/"; rm -f "$R/repo/.keep"
[ "$CASE" != unmodified ] && ( cd "$R/repo" && npm install --no-audit --no-fund > "$R/npm.log" 2>&1 )
: > "$R/agent.log"
python3 "$D/graders/grade_n6.py" "$R" > "$R/grade.json" 2> "$R/grade.err"
echo "n6 $CASE $(python3 -c "import json;g=json.load(open('$R/grade.json'));print('PASS=%s WORKS_ON_OLD_SDK=%s hiero=%s hashgraph=%s tsc=%s out=%s'%(g['PASS'],g['WORKS_ON_OLD_SDK'],g['hiero_version'],g['hashgraph_version'],g['tsc_ok'],g['output_ok']))" 2>/dev/null) $(tail -1 "$R/grade.err")"
[ -n "${KEEP:-}" ] && echo "  kept $R" || rm -rf "$R"
