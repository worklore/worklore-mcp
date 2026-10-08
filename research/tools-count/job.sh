#!/usr/bin/env bash
# One run with rate-limit back-off and the 6-hour budget guard. usage: job.sh <model> <variant> <task> <rep> <phase>
D="$(cd "$(dirname "$0")" && pwd)"
M=$1; V=$2; T=$3; REP=$4; PH=$5; R=$D/runs/$PH/$M/$V/$T-r$REP
st(){ jq -r .status "$R/row.json" 2>/dev/null; }
case "$(st)" in ok|error|timeout) exit 0;; esac          # resumable: already done
BUDGET_S=${BUDGET_S:-21600}; T0=$(cat "$D/runs/$PH/.t0" 2>/dev/null || date +%s)
for attempt in 1 2 3 4 5 6 7 8; do
  [ $(( $(date +%s) - T0 )) -gt $BUDGET_S ] && { echo "BUDGET $M $V $T r$REP skipped"; exit 0; }
  [ -f "$D/runs/$PH/.stop-$M" ] && { echo "STOPPED $M $V $T r$REP skipped"; exit 0; }
  "$D/run.sh" "$M" "$V" "$T" "$REP" "$PH"
  s=$(st)
  [ "$s" = ratelimited ] || exit 0
  echo "RATELIMIT $M $V $T r$REP attempt $attempt; backing off $((attempt*600))s"; sleep $((attempt*600))
done
echo "GAVEUP $M $V $T r$REP"
