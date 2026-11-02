# Summary of Changes

## What was changed
In [`gen.py`](file:///private/tmp/h-dOiITX/gen.py#L10-L13), updated `hr_target(step)` to return `{"units": "%lthr", "start": lo, "end": hi}` instead of `{"units": "%lthr", "value": lo, "end": hi}`:

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

## Why
When Intervals.icu exports structured workouts to Garmin (FIT format):
- Using `{"value": lo, "end": hi}` routes the target as a Lap-HR / zone-mapped target, which causes the Garmin watch to clamp the corridor to its own locally configured HR zone boundaries.
- Using `{"start": lo, "end": hi}` causes Intervals.icu to treat the target as an Instant-HR corridor, exporting the computed raw bpm values based on the athlete's threshold stored in Intervals.icu rather than snapping to watch zone boundaries.
