#!/usr/bin/env bash
# usage: lane.sh <agent> [reps]  — reps in the OUTER loop, so a lane stopped early still holds complete
# repetitions for every cell. Story order rotates per agent so lanes do not all hit the same fixture at
# once. A run that died on a usage limit or a provider outage (meta "limit":true, or exit 3) is deleted
# and redone on a later pass; passes repeat, 30 minutes apart, until every cell has a result or
# LIMIT_PASSES is reached.
D="$(cd "$(dirname "$0")" && pwd)"
A=$1; REPS=${2:-5}
ALL=(s1 s3 s7 s8 s10 s11)
ARMS=(none-en example-en none-ru example-ru example-ruru)
case $A in claude-opus) k=0;; claude-sonnet) k=2;; claude-haiku) k=4;; codex-sol) k=1;; codex-sol-low) k=3;; agy-flash-low) k=0;; agy-oss) k=3;; agy-argon-high) k=5;; agy-argon-low) k=2;; *) k=0;; esac
ORDER=("${ALL[@]:$k}" "${ALL[@]:0:$k}")
LIMIT_PASSES=10
bad() { [ -f "$1/meta.json" ] && grep -qE '"limit":true|"exit_code":3[,}]' "$1/meta.json"; }
one() { # one <story> <arm> <rep>
  local R="$D/runs/$1-$A-$2-r$3"
  if [ -f "$R/grade.json" ]; then bad "$R" || return; echo "REDO $1 $2 r$3" >> "$D/lane-$A.out"; rm -rf "$R"; fi
  "$D/run.sh" "$1" "$A" "$2" "$3" >> "$D/lane-$A.out" 2>&1
  if bad "$R"; then echo "LIMIT $1 $2 r$3 (will redo)" >> "$D/lane-$A.out"; rm -rf "$R"; fi
}
missing() { local n=0; for REP in $(seq 1 "$REPS"); do for S in "${ALL[@]}"; do for ARM in "${ARMS[@]}"; do
  [ -f "$D/runs/$S-$A-$ARM-r$REP/grade.json" ] || n=$((n+1)); done; done; done; echo $n; }
REPSEQ=$(seq 1 "$REPS"); [ "${REV:-0}" = 1 ] && REPSEQ=$(seq "$REPS" -1 1)
pass=0
while :; do
  for REP in $REPSEQ; do for S in "${ORDER[@]}"; do for ARM in "${ARMS[@]}"; do one "$S" "$ARM" "$REP"; done; done; done
  pass=$((pass+1)); m=$(missing)
  [ "$m" = 0 ] && break
  [ "$pass" -ge "$LIMIT_PASSES" ] && { echo "LANE_GAVE_UP after $pass passes, $m cells missing" >> "$D/lane-$A.out"; break; }
  echo "pass $pass done, $m cells missing; sleeping 30 min" >> "$D/lane-$A.out"; sleep 1800
done
echo LANE_DONE >> "$D/lane-$A.out"
