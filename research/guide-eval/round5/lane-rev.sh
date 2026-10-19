#!/usr/bin/env bash
# Same as lane.sh but in reverse order (notes first, stories reversed), skipping any run that has started.
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/45aea092-d156-403e-85fa-11e392426b83/scratchpad/guide-eval-r5
A=$1
one() { [ -d "$D/runs/$1-$A-$2-r1" ] && return
  if [ "$1" = s6 ]; then python3 "$D/lock.py" "$D/s6.lock" "$D/run.sh" $1 $A $2 1 >> "$D/lane-$A.out" 2>&1
  else "$D/run.sh" $1 $A $2 1 >> "$D/lane-$A.out" 2>&1; fi; }
for S in s6 s5 s4 s3 s2 s1; do one $S notes; done
for S in s6 s5 s4 s3 s2 s1; do for ARM in example follow none; do one $S $ARM; done; done
echo LANE_DONE >> "$D/lane-$A.out"
