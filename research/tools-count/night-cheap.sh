#!/usr/bin/env bash
# Cheap-model phase (2026-10-14): same tasks, sizes and grouped variant as "full", 2 reps, cheapest model per harness.
# usage: night-cheap.sh [start HH:MM]   — waits until that local time, keeps the Mac awake, runs 3 lanes in parallel.
D="$(cd "$(dirname "$0")" && pwd)"
AT=${1:-23:30}
now=$(date +%s); t=$(date -d "today $AT" +%s); [ $t -lt $now ] && t=$now
echo "waiting until $(date -d @$t)"; sleep $((t-now))
V="5 10 15 20 25 30 35 40 45 50 75 100 GROUPED"
(MODEL_ID=claude-haiku-5-5     "$D/lane.sh" claude cheap 2 3 $V > "$D/runs-cheap-claude.out" 2>&1) &
(MODEL_ID=gpt-reserve          "$D/lane.sh" codex  cheap 2 3 $V > "$D/runs-cheap-codex.out" 2>&1) &
(MODEL_ID=gemini-3.8-flash-low "$D/lane.sh" gemini cheap 2 3 $V > "$D/runs-cheap-gemini.out" 2>&1) &
wait
python3 "$D/aggregate.py"
"$D/.venv/bin/python" "$D/analyze.py" cheap
echo "NIGHT_DONE $(date)"
