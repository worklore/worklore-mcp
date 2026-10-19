# Changes to Workout Generator

## What Changed
In `gen.py`, modified `hr_target()` to use the key `"start"` instead of `"value"` for the lower bound of the heart rate target:

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

## Why
In Intervals.icu's API:
- Using `{"units": "%lthr", "value": <lo>, "end": <hi>}` routes the step as a Lap-HR / zone-mapped target during FIT export to Garmin Connect. The watch then clamps the target range to its own local zone boundaries (e.g. Forerunner 965 auto-detected LTHR zones).
- Using `{"units": "%lthr", "start": <lo>, "end": <hi>}` routes the target as an Instant-HR corridor. Intervals.icu calculates the exact target bpm values using the athlete's stored LTHR in Intervals (e.g. 172) and exports the exact corridor to Garmin, preventing the watch from clamping to its own local zones.
