#!/usr/bin/env bash
# usage: lane.sh <model> <phase> <reps> <parallel> <variants...>
D=~/projects/worklore/research/2026-10-07-tool-count
M=$1; PH=$2; REPS=$3; PAR=$4; shift 4; VARS=("$@")
mkdir -p "$D/runs/$PH"; [ -f "$D/runs/$PH/.t0" ] || date +%s > "$D/runs/$PH/.t0"
TASKS=$(jq -r '.tasks[].id' "$D/tasks.json")
for REP in $(seq 1 $REPS); do for T in $TASKS; do for V in "${VARS[@]}"; do echo "$M $V $T $REP $PH"; done; done; done \
  | xargs -P "$PAR" -L 1 "$D/job.sh"
python3 "$D/aggregate.py" > /dev/null
echo "LANE_DONE $M $PH"
