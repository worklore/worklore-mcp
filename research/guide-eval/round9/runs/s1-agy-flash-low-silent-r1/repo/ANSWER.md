# Root Cause and Fix for Clamped HR Ranges

## What was changed
In [`gen.py`](file:///private/tmp/h-35RIwT/gen.py), updated `hr_target(step)`:
- Changed `"value": lo` to `"start": lo`.
- Kept `"units": "%lthr"` and `"end": hi`.

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

## Why this change was made
In the Intervals.icu `workout_doc` JSON schema:
1. When target ranges are defined, Intervals.icu uses `start` and `end` (e.g. `{"start": lo, "end": hi, "units": "%lthr"}`).
2. Previously, `gen.py` emitted `{"value": lo, "end": hi, "units": "%lthr"}`. Because `value` was supplied instead of `start`, Intervals.icu treated the target as a single fixed target at `value` (`lo`), ignoring `end`.
3. When Intervals.icu exports a single-value target to Garmin, it identifies which zone the single value falls into and maps the step as that preset zone. In the Garmin FIT export, `target_value` is set to that zone number rather than `0` (custom target boundaries). Consequently, the watch displayed the entire preset zone band (e.g., Zone 2: 118–137 bpm for Warm-up and Cool-down, Zone 4: 151–162 bpm for Tempo, Zone 3: 137–151 bpm for Float) clamped to the watch's own configured zone boundaries.
4. Using `start` and `end` instructs Intervals.icu to export a custom target corridor (`target_value = 0` with custom low and high bounds), preserving the exact planned heart rate range on the watch.
