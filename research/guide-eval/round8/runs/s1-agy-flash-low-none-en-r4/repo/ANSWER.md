# Changes and Explanation

## What was changed
In [`gen.py`](file:///tmp/h-CK7OyP/gen.py), in the `hr_target(step)` function:
- Changed the dictionary key for the lower bound of the HR corridor from `"value"` to `"start"`:
  ```python
  # Before
  return {"units": "%lthr", "value": lo, "end": hi}

  # After
  return {"units": "%lthr", "start": lo, "end": hi}
  ```

## Why this fixes the issue
When exporting structured workouts from Intervals.icu to Garmin watches via FIT file conversion:
- Using `{"value": lo, "end": hi}` causes Intervals.icu/Garmin FIT export to treat the target range as a zone-mapped or lap target. Under this format, the Garmin device clamps the bounds to the device's locally configured HR zones (derived from the watch's auto-detected LTHR) rather than preserving the specific corridor planned in the workout.
- Using `{"start": lo, "end": hi}` specifies an explicit "Instant-HR" range target corridor in Intervals.icu's workout schema. This ensures Intervals.icu exports the target as a raw corridor calculated from the athlete's threshold settings, preventing the watch from clamping the range to its own internal zone boundaries.
