# tri-planner

Generates structured triathlon workouts and pushes them to Intervals.icu, which
exports them to the athlete's Garmin watch through Garmin Connect.

- `gen.py` turns a plan (`plans/*.json`) into the body for
  `POST /api/v1/athlete/{id}/events` (an event with `workout_doc`).
- `push.sh` posts it (needs `INTERVALS_API_KEY` and `ATHLETE_ID`).
- `readback/` holds what the API returned for the last pushed event and
  notes on what the watch displayed.

Set `lthr_bpm` in each plan to the athlete's current LTHR. HR targets in plans
are percentages of that value. The generator converts them to bpm and applies
the 100 bpm offset observed in the Intervals-to-Garmin export; update the plan
when the athlete's LTHR changes.

```
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```
