# Summary of Changes

## What was changed
In [`gen.py`](file:///tmp/h-Ad3IOv/gen.py), in the `hr_target(step)` function:
- Changed the dictionary key for the lower bound from `"value"` to `"start"`.
- The returned target dictionary changed from:
  ```python
  {"units": "%lthr", "value": lo, "end": hi}
  ```
  to:
  ```python
  {"units": "%lthr", "start": lo, "end": hi}
  ```

## Why it was changed
When exporting workout definitions (`workout_doc`) to Garmin FIT files:
- An HR step formatted with `{"value": ..., "end": ...}` is treated by the Intervals.icu FIT exporter as a zone-mapped / lap-average target. Garmin Connect / the Garmin device then snaps or clamps the target bounds to the watch's own internal LTHR/HR zones instead of using the custom corridor.
- Using `{"start": ..., "end": ...}` triggers the export format for an Instant-HR corridor. Intervals computes the explicit target bounds from the athlete's configured threshold (LTHR 172) and exports custom low and high boundaries, preventing the watch from clamping them to its own local zone thresholds.
