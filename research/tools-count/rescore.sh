#!/usr/bin/env bash
# Re-score every finished run from its saved logs (scoring is deterministic), then rebuild results.csv.
D="$(cd "$(dirname "$0")" && pwd)"
for R in "$D"/runs/*/*/*/*/; do
  [ -f "$R/meta.json" ] || continue
  python3 "$D/score.py" "$R" > "$R/row.json.new" 2> "$R/score.err" && mv "$R/row.json.new" "$R/row.json"
done
# pilot1 rows keep their phase label
for f in "$D"/runs/pilot1/*/*/*/row.json; do jq -c '.phase="pilot1"' "$f" > "$f.t" && mv "$f.t" "$f"; done
python3 "$D/aggregate.py"
