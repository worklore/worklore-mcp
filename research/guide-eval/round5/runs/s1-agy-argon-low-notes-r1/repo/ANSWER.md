# Fix for HR Ranges Clamped to Watch Zones

## What Changed

In `gen.py` (`hr_target`), changed the lower bound key of the `hr` target object from `"value"` to `"start"`:

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

## Why

When Intervals.icu exports a workout to Garmin FIT format, the key name used for the lower bound of the HR target controls the FIT export mode:

- `{"units": "%lthr", "value": lo, "end": hi}` routes the target as a **Lap-HR / zone-mapped** target, which causes the Garmin watch to clamp the target corridor to its own local HR zone boundaries.
- `{"units": "%lthr", "start": lo, "end": hi}` exports the target as an **Instant-HR corridor**, where Intervals.icu computes the exact BPM range from its stored athlete LTHR at FIT-export time and the watch displays that exact BPM range rather than snapping to local watch zones.
