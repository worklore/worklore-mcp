#!/usr/bin/env bash
# usage: lane.sh <cc|agy> <sonnet|opus> <reps>
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/3bfdd3c9-cfe2-4fd1-a8b7-ce52b613a3aa/scratchpad/harness-eval
H=$1; MD=$2; N=$3; OUT=$D/lane-$H-$MD.out
for REP in $(seq 1 $N); do for S in s1 s3; do for ARM in without with; do
  "$D/run.sh" $S $H $MD $ARM $REP >> "$OUT" 2>&1
done; done; done
echo LANE_DONE >> "$OUT"
