#!/usr/bin/env bash
# Relaunch lanes that gave up on a subscription limit (5-hour window), once each lane's first run has ended.
D="$(cd "$(dirname "$0")" && pwd)"; cd "$D"
relaunch() { # relaunch <agent> <task>
  local O="lane-$1-$2.out"
  until tail -1 "$O" | grep -q LANE_DONE; do sleep 120; done
  grep -q LANE_GAVE_UP "$O" || return 0
  [ "$(grep -c RELAUNCH "$O")" -ge 1 ] && return 0
  echo "RELAUNCH $(date '+%F %T')" >> "$O"
  LIMIT_PASSES=10 ./lane.sh "$1" "$2"
}
relaunch codex-sol-low h & relaunch codex-sol-low p & relaunch kimi-k31 h & relaunch kimi-k31 p &
wait; date > relaunch.finished
