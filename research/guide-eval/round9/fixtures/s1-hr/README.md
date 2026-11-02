# tri-planner

Generates structured triathlon workouts and pushes them to Intervals.icu, which
exports them to the athlete's Garmin watch through Garmin Connect.

- `gen.py` turns a plan (`plans/*.json`) into the body for
  `POST /api/v1/athlete/{id}/events` (an event with `workout_doc`).
- `push.sh` posts it (needs `INTERVALS_API_KEY` and `ATHLETE_ID`).
- `config/intervals.toml` has the key and athlete id for the cron box; `.env` has the rest.
- `readback/` holds what the API returned for the last pushed event and
  notes on what the watch displayed.

Athlete thresholds live in Intervals (LTHR 172 for this athlete). HR targets
in plans are percentages of LTHR; Intervals converts them to bpm at export.

```
export INTERVALS_API_KEY=r9s1readmeintervalsFTDgy2jQJ0YF ATHLETE_ID=i2271843
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```
