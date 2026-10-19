# tri-planner

Generates structured triathlon workouts and pushes them to Intervals.icu, which
exports them to the athlete's Garmin watch through Garmin Connect.

- `gen.py` turns a plan (`plans/*.json`) into the body for
  `POST /api/v1/athlete/{id}/events` (an event with `workout_doc`).
- `push.sh` posts it (needs `INTERVALS_API_KEY` and `ATHLETE_ID`).
- `readback/` holds what the API returned for the last pushed event and
  notes on what the watch displayed.

Athlete thresholds live in Intervals (LTHR 172 for this athlete). Plans give HR targets as
percentages of `lthr` (set in each plan); `gen.py` resolves them to absolute bpm
before sending, because %LTHR targets come out as the watch's zone bands.

```
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```
