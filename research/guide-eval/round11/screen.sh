#!/usr/bin/env bash
# The story screen (screen.md): each candidate x claude-haiku, codex-sol-low, agy-flash-low x none, story x 3 reps.
# usage: nohup ./screen.sh n1 n2 n3 n4 > screen.out 2>&1 &
# Runs are named <id>-<agent>-<arm>-r<rep> under runs/, like every other round 11 run. A run marked limit=true is redone
# once at the end of the screen.
D="$(cd "$(dirname "$0")" && pwd)"
IDS=("$@"); [ ${#IDS[@]} -eq 0 ] && { echo "usage: screen.sh <id>..."; exit 2; }
AGENTS=(claude-haiku codex-sol-low agy-flash-low)
for rep in 1 2 3; do
  for s in "${IDS[@]}"; do
    for a in "${AGENTS[@]}"; do
      for arm in none story; do
        EVAL_NO_SECRETS=1 "$D/run.sh" "$s" "$a" "$arm" "$rep"
      done
    done
  done
done
for m in "$D"/runs/*/meta.json; do
  grep -q '"limit":true' "$m" || continue
  read -r s a arm rep < <(python3 -c 'import json,sys;m=json.load(open(sys.argv[1]));print(m["story"],m["agent"],m["arm"],m["rep"])' "$m")
  case " ${IDS[*]} " in *" $s "*) EVAL_NO_SECRETS=1 "$D/run.sh" "$s" "$a" "$arm" "$rep";; esac
done
echo "screen done $(date '+%F %T')"
