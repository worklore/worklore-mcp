# Changes Made and Analysis

## What Was Changed
In [`gen.py`](file:///tmp/h-k6SaQU/gen.py) inside `hr_target()`:
Changed the dictionary key for the lower bound of the HR target corridor from `"value"` to `"start"`:
```python
# Before
return {"units": "%lthr", "value": lo, "end": hi}

# After
return {"units": "%lthr", "start": lo, "end": hi}
```

## Why It Was Changed
In Intervals.icu's workout schema and FIT exporter:
- Target shape `{"units": "%lthr", "value": lo, "end": hi}` is treated by the FIT export engine as a **Lap-HR / zone-mapped target**. In this mode, Garmin watches clamp the target range to their own local (and often stale or auto-detected) HR zones rather than the planned corridor.
- Target shape `{"units": "%lthr", "start": lo, "end": hi}` switches Intervals' FIT export into an **Instant-HR target corridor**. In this mode, Intervals computes the raw bpm values using the athlete's threshold (LTHR) configured in Intervals and exports those exact bounds to the watch, making the corridor drift-immune and independent of the watch's local zone settings.

## Colleague's Note: What Applied and What Was Ignored

### Parts that applied:
- **`start` vs. `value` key name**: The observation that lower bound key `"value"` routes as a Lap-HR/zone-mapped target (causing Garmin watch zone clamping) while `"start"` routes as an Instant-HR corridor with exact calculated bpm targets directly explained and solved our issue.
- **Keeping `units: "%lthr"` with percentages**: The colleague confirmed that `units: "%lthr"` with percentage bounds (`lo`, `hi`) is the correct unit representation because Intervals calculates the bpm targets against the Intervals athlete LTHR at FIT export time, whereas using raw `bpm` or `start_bpm`/`end_bpm` fails.

### Parts that were ignored:
- **Intervals text grammar description (`description` field)**: The notes regarding step rendering in the Intervals web UI via text descriptions (e.g. `m` vs `mtr`, repeat syntax, bare `Z2`, leading digits) were not relevant to the bug at hand, as the prompt specifically addressed fixing the watch HR range clamping in the JSON workout generator.
- **External API reproduction steps / credentials**: The testing steps involving posting live events (`POST /api/v1/athlete/{id}/events`), Garmin Connect syncing, and athlete ID/API credentials were not applicable per the ground rules to work strictly locally without deploying or calling external services.
