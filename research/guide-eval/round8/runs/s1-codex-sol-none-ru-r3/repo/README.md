# tri-planner

Generates structured triathlon workouts and pushes them to Intervals.icu, which
exports them to the athlete's Garmin watch through Garmin Connect.

- `gen.py` turns a plan (`plans/*.json`) into the body for
  `POST /api/v1/athlete/{id}/events` (an event with `workout_doc`).
- `push.sh` posts it (needs `INTERVALS_API_KEY` and `ATHLETE_ID`).
- `readback/` holds what the API returned for the last pushed event and
  notes on what the watch displayed.

Plans include the LTHR used to calculate their HR targets (`lthr_bpm`). The
generator rounds each percentage boundary to bpm and emits a custom bpm
corridor as a midpoint and half-width. Update `lthr_bpm` when the planned
threshold changes; the watch's own zones do not define these corridors.

```
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```
