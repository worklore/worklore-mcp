#!/usr/bin/env bash
# usage: lane.sh <agent>  — six stories × (none, follow, example), then the notes arm for all six.
# Story order rotates per agent so lanes do not all reach s6 at once; s6 runs are serialised with a
# lock because an agent may `pkill -f server.py` and would kill another lane's server.
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/45aea092-d156-403e-85fa-11e392426b83/scratchpad/guide-eval-r5
A=$1
ALL=(s1 s2 s3 s4 s5 s6)
case $A in claude-opus) k=0;; claude-sonnet) k=2;; claude-haiku) k=4;; codex-sol) k=1;; codex-sol-low) k=3;; agy-argon-high) k=5;; agy-argon-low) k=2;; agy-flash-low) k=0;; agy-oss) k=3;; *) k=0;; esac
ORDER=("${ALL[@]:$k}" "${ALL[@]:0:$k}")
one() { # one <story> <arm>
  [ -f "$D/runs/$1-$A-$2-r1/grade.json" ] && return
  if [ "$1" = s6 ]; then python3 "$D/lock.py" "$D/s6.lock" "$D/run.sh" $1 $A $2 1 >> "$D/lane-$A.out" 2>&1
  else "$D/run.sh" $1 $A $2 1 >> "$D/lane-$A.out" 2>&1; fi
}
for S in "${ORDER[@]}"; do for ARM in none follow example; do one $S $ARM; done; done
for S in "${ORDER[@]}"; do one $S notes; done
echo LANE_DONE >> "$D/lane-$A.out"
