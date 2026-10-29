# tri-planner

Generates structured triathlon workouts and pushes them to Intervals.icu, which
exports them to the athlete's Garmin watch through Garmin Connect.

- `gen.py` turns a plan (`plans/*.json`) into the body for
  `POST /api/v1/athlete/{id}/events` (an event with `workout_doc`).
- `push.sh` posts it (needs `INTERVALS_API_KEY` and `ATHLETE_ID`).
- `readback/` holds what the API returned for the last pushed event and
  notes on what the watch displayed.

Plans specify `lthr_bpm` (172 for this athlete) and HR targets as percentages
of it. The generator computes rounded bpm bounds before export and applies the
100 bpm offset required by the observed Intervals-to-Garmin export. Update
`lthr_bpm` when the planned threshold changes.

```
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```
