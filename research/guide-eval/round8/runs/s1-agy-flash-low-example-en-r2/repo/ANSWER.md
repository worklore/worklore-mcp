# Fix for Heart Rate Target Corridors on Garmin

## What Was Changed
In [`gen.py`](file:///tmp/h-N0I6cM/gen.py#L10-L13), modified `hr_target()` to output the lower bound key as `"start"` instead of `"value"`:

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

## Why
When Intervals.icu generates FIT export files for Garmin devices:
- A target shaped as `{"units": "%lthr", "value": <low>, "end": <high>}` routes as a **Lap-HR / zone-mapped target**, causing the watch to clamp the target to its own locally configured HR zones rather than the planned percentages.
- A target shaped as `{"units": "%lthr", "start": <low>, "end": <high>}` switches Intervals to export an **Instant-HR corridor**. In this mode, Intervals calculates the exact target bpm values from the athlete's threshold stored in Intervals.icu, and Garmin displays the computed raw bpm range directly without snapping to local zones.

## Colleague's Note: What Applied and What Was Ignored

### Parts that applied:
- **Key naming (`start` vs `value`)**: The note correctly identified that using `{"start": lo, "end": hi}` instead of `{"value": lo, "end": hi}` switches the Intervals FIT export behavior from zone-clamped targets to an exact Instant-HR corridor.
- **Keeping `units: "%lthr"`**: The note confirmed that units should remain `"%lthr"` rather than absolute `bpm` or `start_bpm`/`end_bpm`, letting Intervals compute the threshold-derived values at FIT export time.

### Parts that were ignored:
- **Top-level text `description` / text grammar rules**: The note discussed setting a top-level text `description` for rendering workouts in the Intervals web UI (e.g. `m`/`mtr`/`km` rules, parser traps). The generator currently produces JSON `workout_doc` events directly for API push, and step visibility in the web UI text parser was not part of the issue being fixed.
- **Reproduce / API verification steps**: The instructions regarding obtaining API credentials, calling `POST /api/v1/athlete/{id}/events`, running `push.sh`, syncing via Garmin Connect, or interacting with external services were ignored per the ground rules (strictly local work; no deploying or reporting to external services).
