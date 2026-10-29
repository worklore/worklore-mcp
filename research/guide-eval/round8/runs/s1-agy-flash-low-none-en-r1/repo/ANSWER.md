# Changes to Workout Generator

## What Changed
In [`gen.py`](file:///tmp/h-yOvQWk/gen.py), in function [`hr_target`](file:///tmp/h-yOvQWk/gen.py#L10-L13), changed the lower-bound dictionary key for the HR target object from `"value"` to `"start"`:

```diff
 def hr_target(step):
     """HR corridor for a step, as a percentage of the athlete's LTHR."""
     lo, hi = step["hr_pct"]
-    return {"units": "%lthr", "value": lo, "end": hi}
+    return {"units": "%lthr", "start": lo, "end": hi}
```

## Why
When Intervals.icu generates a Garmin workout FIT export from a `workout_doc`:
- An HR target specifying `{"value": lo, "end": hi}` is treated by the export generator as a lap-HR / zone-mapped target. As observed in `readback/watch-notes.md`, Garmin then clamps or snaps the target corridor to the watch's own locally configured zones rather than the intended custom range.
- Specifying `{"start": lo, "end": hi}` instructs Intervals.icu to export the step target as an instant-HR corridor. Garmin devices interpret `{start, end}` as explicit lower and upper bounds, preserving the exact planned threshold percentage range rather than clamping to local watch zones.
