#!/usr/bin/env bash
# 8 skills x 3 agents x 3 reps; 2 parallel runs per agent. Resumable (skips runs with a row.json).
D=/Users/valentinakoniukhova/projects/worklore/research/2026-10-14-paste-hash
PHASES=${PHASES:-before}
for A in claude codex gemini; do (
  for PH in $PHASES; do for REP in 1 2 3; do for f in "$D"/skills/*.md; do S=$(basename "$f" .md)
    [ -f "$D/runs/$PH/$A/$S-r$REP/row.json" ] || echo "$A $S $REP $PH"; done; done; done | xargs -P 2 -L 1 "$D/run.sh"
) > "$D/batch-$A.out" 2>&1 & done
wait
python3 "$D/summarize.py" > "$D/summary.md"
echo "HASH_DONE $(date)"
