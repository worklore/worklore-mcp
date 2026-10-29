# tri-planner

Generates structured triathlon workouts and pushes them to Intervals.icu, which
exports them to the athlete's Garmin watch through Garmin Connect.

- `gen.py` turns a plan (`plans/*.json`) into the body for
  `POST /api/v1/athlete/{id}/events` (an event with `workout_doc`).
- `push.sh` posts it (needs `INTERVALS_API_KEY` and `ATHLETE_ID`).
- `readback/` holds what the API returned for the last pushed event and
  notes on what the watch displayed.

Set `lthr_bpm` in each plan to the athlete's current LTHR (172 in the example).
HR ranges in `hr_pct` are percentages of that value. The generator converts
them to whole bpm and writes the exact corridor into each step's text. It does
not send a structured HR target: the observed Garmin export maps `%lthr`
targets to the watch's zone bands, while a prior `bpm` target export displayed
values 100 bpm too high. This keeps the planned corridor in the step instruction
and removes HR target alerts. The step text still needs an on-watch check.

```
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```
