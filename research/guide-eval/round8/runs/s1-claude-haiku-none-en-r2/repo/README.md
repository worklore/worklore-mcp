# tri-planner

Generates structured triathlon workouts and pushes them to Intervals.icu, which
exports them to the athlete's Garmin watch through Garmin Connect.

- `gen.py` turns a plan (`plans/*.json`) into the body for
  `POST /api/v1/athlete/{id}/events` (an event with `workout_doc`).
- `push.sh` posts it (needs `INTERVALS_API_KEY` and `ATHLETE_ID`).
- `readback/` holds what the API returned for the last pushed event and
  notes on what the watch displayed.

Athlete thresholds: LTHR 172 for this athlete. Plans express HR targets as
percentages of LTHR, and `gen.py` converts them to absolute bpm (`LTHR` constant
in `gen.py`) before posting, so the watch does not re-resolve them against its
own auto-detected LTHR/zones.

```
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```
