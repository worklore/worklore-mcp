#!/usr/bin/env bash
# usage: lane.sh <agent>  -- one lane per agent. `asked` gets 3 repetitions, `silent` 1; repetitions in the
# OUTER loop, so a lane stopped early still holds complete repetitions for every cell. Fixture order
# rotates per agent so the three lanes do not hit the same fixture at once. A run that died on a usage
# limit, a provider outage or a sandbox refusal (meta "limit":true, or exit 3) is deleted and redone on a
# later pass; passes repeat, 30 minutes apart, until every cell has a result or LIMIT_PASSES is reached.
D="$(cd "$(dirname "$0")" && pwd)"
A=$1
ALL=(s1 s3 s7 s8 s10 s11)
REPS_asked=3; REPS_silent=1
case $A in claude-opus) k=0;; codex-sol) k=2;; agy-flash-low) k=4;; *) k=0;; esac
ORDER=("${ALL[@]:$k}" "${ALL[@]:0:$k}")
LIMIT_PASSES=10
bad() { [ -f "$1/meta.json" ] && grep -qE '"limit":true|"exit_code":3[,}]' "$1/meta.json"; }
one() { # one <story> <arm> <rep>
  local R="$D/runs/$1-$A-$2-r$3"
  if [ -f "$R/grade.json" ]; then bad "$R" || return; echo "REDO $1 $2 r$3" >> "$D/lane-$A.out"; rm -rf "$R"; fi
  "$D/run.sh" "$1" "$A" "$2" "$3" >> "$D/lane-$A.out" 2>&1
  if bad "$R"; then echo "LIMIT $1 $2 r$3 (will redo)" >> "$D/lane-$A.out"; rm -rf "$R"; fi
}
missing() { local n=0; for S in "${ALL[@]}"; do
  for REP in 1 2 3; do [ -f "$D/runs/$S-$A-asked-r$REP/grade.json" ] || n=$((n+1)); done
  [ -f "$D/runs/$S-$A-silent-r1/grade.json" ] || n=$((n+1)); done; echo $n; }
pass=0
while :; do
  for REP in 1 2 3; do for S in "${ORDER[@]}"; do
    one "$S" asked "$REP"
    [ "$REP" = 1 ] && one "$S" silent 1
  done; done
  pass=$((pass+1)); m=$(missing)
  [ "$m" = 0 ] && break
  [ "$pass" -ge "$LIMIT_PASSES" ] && { echo "LANE_GAVE_UP after $pass passes, $m cells missing" >> "$D/lane-$A.out"; break; }
  echo "pass $pass done, $m cells missing; sleeping 30 min" >> "$D/lane-$A.out"; sleep 1800
done
echo LANE_DONE >> "$D/lane-$A.out"
