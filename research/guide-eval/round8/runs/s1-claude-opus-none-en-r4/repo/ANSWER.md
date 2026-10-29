# HR corridors shown as watch zones: fix

## Cause
`gen.py` wrote each HR corridor as

```json
"hr": {"units": "%lthr", "value": 68, "end": 75}
```

In Intervals.icu's `workout_doc`, a **range** is written as `start` + `end`.
`value` means a **single target**. Intervals read each step as one %LTHR value,
so `end` had no effect. When it exported to Garmin, it sent each single HR
value as a heart-rate *zone* target. The watch then showed that zone's edges
from its own zone table (118–137, 151–162, …). That is why changing the
watch's LTHR moved the bands but never produced 151–160. The API still
accepted the doc and returned it as sent, because the keys are valid JSON.
So the readback looked fine even though it was read differently.

The earlier attempts were also off the target: `start_bpm`/`end_bpm` are not
workout_doc fields, and absolute `bpm` values skip the %LTHR conversion that
the README relies on.

## Change (`gen.py`, `hr_target`)
- A corridor is now `{"units": "%lthr", "start": lo, "end": hi}`. Intervals
  converts it with the athlete's LTHR (172) and exports it as a custom bpm
  range, e.g. Tempo 88–93% → about 151–160.
- If `lo == hi`, it outputs a single `value` (a deliberate single target).
- If `lo > hi`, it raises an error instead of sending an inverted range.

The plan files and `push.sh` are unchanged.

## Not verified
I did not push anything (per the ground rules), so I have not confirmed this
against the live API or the watch. To check: regenerate
(`python3 gen.py plans/tempo-run.json > event.json`), push, sync, and confirm
the watch shows Tempo ≈151–160 and Float ≈129–141. If the steps still appear
as zones, check whether Intervals' Garmin export settings force HR targets
to zones.
