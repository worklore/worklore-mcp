# Changes Made and Explanation

## What Changed
In [`gen.py`](file:///private/tmp/h-VRdYAW/gen.py#L10-L14), updated the dictionary key returned by `hr_target` from `"value"` to `"start"`:

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

## Why
When generating structured workouts for Intervals.icu that export to Garmin devices via FIT files:
- Supplying `{"units": "%lthr", "value": <low>, "end": <high>}` causes Intervals.icu to treat the step as a **Lap-HR / zone-mapped** target. When exported to Garmin FIT format, Garmin clamps the corridor to the watch's own predefined threshold zones (e.g., Z1–Z5) instead of respecting the exact target boundaries planned in the workout.
- Supplying `{"units": "%lthr", "start": <low>, "end": <high>}` flags the step as an **Instant-HR corridor**. In this mode, Intervals calculates the exact target bpm values using the athlete's stored LTHR threshold and exports the precise corridor bounds to the FIT file, rendering the planned bpm range directly on the watch face without zone snapping.
