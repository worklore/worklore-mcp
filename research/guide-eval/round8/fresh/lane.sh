#!/usr/bin/env bash
# usage: fresh/lane.sh <agent>  — 5 reps x 2 arms, reps outer; limit-hit runs redone once after 20 min
F="$(cd "$(dirname "$0")" && pwd)"; A=$1
for pass in 1 2; do
  for REP in 1 2 3 4 5; do for ARM in fresh-ru fresh-en; do
    R=$F/runs/s1-$A-$ARM-r$REP
    if [ -f "$R/grade.json" ] && ! grep -q '"limit":true' "$R/meta.json"; then continue; fi
    "$F/run.sh" "$A" "$ARM" "$REP" >> "$F/lane-$A.out" 2>&1
  done; done
  grep -l '"limit":true' "$F"/runs/s1-$A-*/meta.json >/dev/null 2>&1 || break
  echo "limit hits, sleeping 20 min" >> "$F/lane-$A.out"; sleep 1200
done
echo LANE_DONE >> "$F/lane-$A.out"
