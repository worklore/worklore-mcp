# Changes Made and Why

## What Changed
In [gen.py](file:///tmp/h-a5No1F/gen.py#L10-L13), modified the `hr_target` dictionary generation so the lower bound of the HR target uses the key `"start"` instead of `"value"`:

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

## Why
When exporting workouts to Garmin FIT format, Intervals.icu interprets `{units: "%lthr", value, end}` as a Lap-HR / zone-mapped target. As documented in [readback/watch-notes.md](file:///tmp/h-a5No1F/readback/watch-notes.md), this causes the Garmin watch to clamp HR targets to its own locally stored HR zones rather than the planned target range.

Renaming `"value"` to `"start"` (`{units: "%lthr", start, end}`) tells Intervals.icu to treat the step as an Instant-HR corridor. In FIT export, Intervals calculates the raw bpm bounds based on the athlete's LTHR stored in Intervals.icu, rendering the exact intended bpm targets on the watch and preventing zone-clamping.

## Colleague Note Application
- **Applied**:
  - Key name change for HR targets from `{"value": lo, "end": hi}` to `{"start": lo, "end": hi}` with `{"units": "%lthr"}`. This triggers Intervals.icu's FIT exporter to export an Instant-HR corridor with raw calculated bpm rather than a zone-mapped target clamped by Garmin.
- **Ignored / Not Applicable**:
  - Web UI text grammar description instructions (generating a top-level `description` field with text syntax for the Intervals UI step chart). The existing pipeline and schema in this repo use `workout_doc.steps` exclusively for API workout generation (`gen.py`), and adding top-level text grammar descriptions is not part of the current event generator.
  - Setup and API testing/push steps (OAuth/API keys, creating/deleting events via curl/push.sh, watch sync verification). These were external testing instructions and out-of-scope per ground rules (work only inside current directory, no external service calls).
