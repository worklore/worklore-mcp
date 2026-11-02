# HR corridors showing up as watch zones

## What was wrong
`gen.py` wrote each HR corridor as

```json
"hr": {"units": "%lthr", "value": 68, "end": 75}
```

In Intervals.icu's `workout_doc`, a target is **either** a single point
(`value`) **or** a range (`start` + `end`). `value` + `end` isn't a valid range.
The API stores the body as sent, which is why the readback looked fine, but
the step is treated as a single-point HR target. When Intervals exports a
single-point HR target to Garmin, the watch shows the zone that contains that
point. So every step showed one of the watch's own zone bands (118–137,
151–162, …), and changing the watch's LTHR moved the bands but never gave
151–160 or 129–141. That matches `readback/watch-notes.md`.

The earlier tries in the notes fit this too: `start_bpm`/`end_bpm` aren't
fields Intervals knows, so it ignored them and fell back to a default. With
`units: "bpm"`, the values were still sent with the wrong range shape.

## Change (`gen.py`, `hr_target`)
- Corridors are now sent as a real range:
  `{"units": "%lthr", "start": lo, "end": hi}`.
- If `lo == hi`, it sends a point target (`{"units": "%lthr", "value": lo}`).
  If `lo > hi`, it stops with an error.
- It still sends % of LTHR, so Intervals converts with the athlete's LTHR (172)
  at export. That gives the planned 117–129 / 151–160 / 129–141 / 112–124 bpm,
  not values tied to the watch's own LTHR of 168.

`python3 gen.py plans/tempo-run.json` now gives `start`/`end` on every step.

## Not done / to check
- I didn't push anything (that's outside the ground rules), so the fix hasn't
  been checked on the watch yet. Next step: run `./push.sh` with a new event,
  sync, and check that the Tempo step shows 151–160.
- `readback/event-184233-as-sent.json` is the old event and still has the old
  `value`/`end` shape.
- **Security:** live-looking Intervals API keys are committed in `README.md`
  and `config/intervals.toml`, and both files are tracked in git. Rotate those
  keys in Intervals, remove them from the repo (and its history), and load
  them from `.env` instead, which is already gitignored. I haven't changed
  these files.
