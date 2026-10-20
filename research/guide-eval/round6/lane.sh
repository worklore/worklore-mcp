#!/usr/bin/env bash
# usage: lane.sh <agent>   — runs s1 without then with, for one agent
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/45aea092-d156-403e-85fa-11e392426b83/scratchpad/guide-eval-r6
A=$1
for ARM in without with; do "$D/run.sh" s1 $A $ARM 1 >> "$D/lane-$A.out" 2>&1; done
echo LANE_DONE >> "$D/lane-$A.out"
