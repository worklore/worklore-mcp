#!/usr/bin/env bash
# usage: lane.sh <agent> <task h|p> [reps]
# One lane = one agent on one task (two lanes per agent run in parallel). As in rounds 8 and 11: repetitions in the OUTER
# loop, so a lane stopped early (or read in the morning) still holds complete repetitions for every cell; a run marked
# "limit" is deleted and redone on a later pass; passes repeat 30 minutes apart until every cell has a result.
# Cells per task and agent: none and line in en, ru, uk, es; story in en and ru = 10 cells x reps.
D="$(cd "$(dirname "$0")" && pwd)"
A=$1; S=$2; REPS=${3:-5}
OUT="$D/lane-$A-$S.out"
CELLS=(en:none en:line en:story ru:none ru:line ru:story uk:none uk:line es:none es:line)
# rotate the cell order per agent, so time-of-night effects do not land on the same cell in every lane
case $A in claude-haiku) k=0;; codex-sol-low) k=3;; kimi-k31) k=6;; claude-deepseek) k=8;; *) k=0;; esac
ORDER=("${CELLS[@]:$k}" "${CELLS[@]:0:$k}")
LIMIT_PASSES=${LIMIT_PASSES:-8}
if [ "$A" = claude-deepseek ] && [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  DEEPSEEK_API_KEY="$(bash -c 'source ~/.zshenv >/dev/null 2>&1; printf %s "$DEEPSEEK_API_KEY"')"
  [ -n "$DEEPSEEK_API_KEY" ] || { echo "no DEEPSEEK_API_KEY in ~/.zshenv" | tee -a "$OUT"; exit 1; }
  export DEEPSEEK_API_KEY
fi
stopped() { [ -f "$D/STOP-$A" ] && { echo "LANE_STOPPED: $(tail -1 "$D/STOP-$A")" >> "$OUT"; exit 1; }; }
bad() { [ -f "$1/meta.json" ] && grep -qE '"limit":true' "$1/meta.json"; }
one() { # one <lang> <arm> <rep>
  local R="$D/runs/$S-$1-$A-$2-r$3"
  if [ -f "$R/grade.json" ]; then bad "$R" || return; echo "REDO $S $1 $2 r$3" >> "$OUT"; rm -rf "$R"; fi
  stopped
  "$D/run.sh" "$S" "$1" "$A" "$2" "$3" >> "$OUT" 2>&1
  if bad "$R"; then echo "LIMIT $S $1 $2 r$3 (will redo)" >> "$OUT"; rm -rf "$R"; fi
  stopped
}
missing() { local n=0 c; for REP in $(seq 1 "$REPS"); do for c in "${CELLS[@]}"; do
  [ -f "$D/runs/$S-${c%%:*}-$A-${c##*:}-r$REP/grade.json" ] || n=$((n+1)); done; done; echo $n; }
pass=0
while :; do
  for REP in $(seq 1 "$REPS"); do for c in "${ORDER[@]}"; do one "${c%%:*}" "${c##*:}" "$REP"; done; done
  pass=$((pass+1)); m=$(missing)
  [ "$m" = 0 ] && break
  [ "$pass" -ge "$LIMIT_PASSES" ] && { echo "LANE_GAVE_UP after $pass passes, $m cells missing" >> "$OUT"; break; }
  echo "pass $pass done, $m cells missing; sleeping 30 min" >> "$OUT"; sleep 1800
done
echo LANE_DONE >> "$OUT"
