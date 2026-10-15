#!/usr/bin/env bash
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/3bfdd3c9-cfe2-4fd1-a8b7-ce52b613a3aa/scratchpad/mp-eval
for ARM in without with; do "$D/run.sh" $1 $ARM >> "$D/lane-$1.out" 2>&1; done
echo LANE_DONE >> "$D/lane-$1.out"
