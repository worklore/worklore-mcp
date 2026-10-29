# tri-planner

Generates structured triathlon workouts and pushes them to Intervals.icu, which
exports them to the athlete's Garmin watch through Garmin Connect.

- `gen.py` turns a plan (`plans/*.json`) into the body for
  `POST /api/v1/athlete/{id}/events` (an event with `workout_doc`).
- `push.sh` posts it (needs `INTERVALS_API_KEY` and `ATHLETE_ID`).
- `readback/` holds what the API returned for the last pushed event and
  notes on what the watch displayed.

Plans specify LTHR in bpm and HR corridors as percentages of it. The generator
converts each corridor to bpm in the step text. Intervals/Garmin may replace
structured HR targets with the watch's zone boundaries, so these steps do not
set HR alerts; the planned range remains visible in the step instruction.

```
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```
