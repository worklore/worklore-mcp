# tri-planner

Generates structured triathlon workouts and pushes them to Intervals.icu, which
exports them to the athlete's Garmin watch through Garmin Connect.

- `gen.py` turns a plan (`plans/*.json`) into the body for
  `POST /api/v1/athlete/{id}/events` (an event with `workout_doc`).
- `push.sh` posts it (needs `INTERVALS_API_KEY` and `ATHLETE_ID`).
- `readback/` holds what the API returned for the last pushed event and
  notes on what the watch displayed.

HR targets in plans are percentages of the plan's `lthr_bpm`. The generator
converts them to BPM and applies the export correction observed on the Garmin
watch. Keep `lthr_bpm` in each plan aligned with the athlete's current LTHR.

```
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```
