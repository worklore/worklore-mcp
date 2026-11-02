# Changes and Rationale

## What Changed
In [`gen.py`](file:///private/tmp/h-mEY0xg/gen.py#L10-L14), updated `hr_target(step)` to use `"start"` instead of `"value"` for the lower bound of the HR target:

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

## Why
When Intervals.icu exports workouts to Garmin FIT format:
- Supplying `{"units": "%lthr", "value": lo, "end": hi}` causes Intervals.icu to treat the step as a Lap-HR / zone-mapped target. As observed in [`readback/watch-notes.md`](file:///private/tmp/h-mEY0xg/readback/watch-notes.md), the Garmin watch clamps these targets to its own preconfigured HR zone boundaries rather than using the custom planned corridor.
- Supplying `{"units": "%lthr", "start": lo, "end": hi}` tells Intervals.icu to emit an Instant-HR corridor target. In this mode, Intervals calculates the exact bpm corridor from the athlete's configured threshold and exports raw target bounds to the watch, preventing the watch from clamping to local zone edges.
