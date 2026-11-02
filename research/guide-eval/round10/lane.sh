#!/usr/bin/env bash
# usage: lane.sh <agent>  -- one lane per agent: 2 variants x 3 arms x 3 reps, repetitions in the OUTER loop.
# A run that died on a usage limit, a provider outage or a sandbox refusal (meta "limit":true, or exit 3)
# is deleted and redone on a later pass; passes repeat, 30 minutes apart, until every cell has a result
# or LIMIT_PASSES is reached.
D="$(cd "$(dirname "$0")" && pwd)"
A=$1
VARIANTS=(shell env); ARMS=(plain xray tool); REPS=3
case $A in claude-opus) ORDER=(plain xray tool);; codex-sol) ORDER=(xray tool plain);; *) ORDER=(tool plain xray);; esac
LIMIT_PASSES=10
bad() { [ -f "$1/meta.json" ] && grep -qE '"limit":true|"exit_code":3[,}]' "$1/meta.json"; }
one() { # one <variant> <arm> <rep>
  local R="$D/runs/$1-$A-$2-r$3"
  if [ -f "$R/grade.json" ]; then bad "$R" || return; echo "REDO $1 $2 r$3" >> "$D/lane-$A.out"; rm -rf "$R"; fi
  "$D/run.sh" "$1" "$A" "$2" "$3" >> "$D/lane-$A.out" 2>&1
  if bad "$R"; then echo "LIMIT $1 $2 r$3 (will redo)" >> "$D/lane-$A.out"; rm -rf "$R"; fi
}
missing() { local n=0; for V in "${VARIANTS[@]}"; do for ARM in "${ARMS[@]}"; do for REP in $(seq 1 $REPS); do
  [ -f "$D/runs/$V-$A-$ARM-r$REP/grade.json" ] || n=$((n+1)); done; done; done; echo $n; }
pass=0
while :; do
  for REP in $(seq 1 $REPS); do for ARM in "${ORDER[@]}"; do for V in "${VARIANTS[@]}"; do one "$V" "$ARM" "$REP"; done; done; done
  pass=$((pass+1)); m=$(missing)
  [ "$m" = 0 ] && break
  [ "$pass" -ge "$LIMIT_PASSES" ] && { echo "LANE_GAVE_UP after $pass passes, $m cells missing" >> "$D/lane-$A.out"; break; }
  echo "pass $pass done, $m cells missing; sleeping 30 min" >> "$D/lane-$A.out"; sleep 1800
done
echo LANE_DONE >> "$D/lane-$A.out"
