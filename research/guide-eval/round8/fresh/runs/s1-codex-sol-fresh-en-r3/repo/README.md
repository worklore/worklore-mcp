# tri-planner

Generates structured triathlon workouts and pushes them to Intervals.icu, which
exports them to the athlete's Garmin watch through Garmin Connect.

- `gen.py` turns a plan (`plans/*.json`) into the body for
  `POST /api/v1/athlete/{id}/events` (an event with matching `description`
  and `workout_doc` workout steps).
- `push.sh` posts it (needs `INTERVALS_API_KEY` and `ATHLETE_ID`).
- `readback/` holds what the API returned for the last pushed event and
  notes on what the watch displayed.

Athlete thresholds live in Intervals (LTHR 172 for this athlete). HR targets
in plans are percentage ranges of LTHR; Intervals converts them to bpm at
export. The generated description requests instant HR targets for the watch.

```
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```
