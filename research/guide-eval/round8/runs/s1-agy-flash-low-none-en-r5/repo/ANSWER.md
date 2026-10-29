# HR Target Range Fix

## What Changed
In [`gen.py`](file:///tmp/h-8Bt5eR/gen.py#L10-L14), changed the lower bound key in the step's `hr` target dictionary from `"value"` to `"start"`:

```python
# Before
return {"units": "%lthr", "value": lo, "end": hi}

# After
return {"units": "%lthr", "start": lo, "end": hi}
```

## Why
When Intervals.icu generates a Garmin FIT workout export from `workout_doc`:
- An HR target formatted with `{"value": ..., "end": ...}` is treated as a zone-mapped target (Lap HR target), causing the Garmin watch to clamp the target boundaries to its own internal LTHR zones.
- Using `{"start": ..., "end": ...}` switches the target into an Instant-HR corridor. In this mode, Garmin displays the exact raw bpm range calculated by Intervals.icu from the athlete's planned `%lthr` rather than snapping to the watch's local zone boundaries.
