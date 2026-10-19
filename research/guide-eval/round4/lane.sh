#!/usr/bin/env bash
# usage: lane.sh <agent> [reps]   — runs s1 and s4, without then with, for one agent
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/45aea092-d156-403e-85fa-11e392426b83/scratchpad/guide-eval-r4
A=$1; N=${2:-1}
for REP in $(seq 1 $N); do for S in s1 s4; do for ARM in without with; do
  "$D/run.sh" $S $A $ARM $REP >> "$D/lane-$A.out" 2>&1
done; done; done
echo LANE_DONE >> "$D/lane-$A.out"
