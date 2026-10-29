# Fix for HR Range Clamping on Garmin

## What was changed

In [`gen.py`](file:///tmp/h-yeqkoo/gen.py#L10-L14), updated the `hr_target(step)` function to key the corridor's lower bound using `"start"` instead of `"value"`:

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

## Why it was changed

In Intervals.icu's workout schema and FIT export engine:
- Target objects shaped as `{"units": "%lthr", "value": <lo>, "end": <hi>}` route through FIT export as Lap-HR / zone-mapped targets. When synced to Garmin watches, the watch clamps the targets to its own locally stored HR zones rather than rendering the intended raw corridors.
- Target objects shaped as `{"units": "%lthr", "start": <lo>, "end": <hi>}` trigger Intervals.icu's Instant-HR corridor export mode. Intervals converts the `%lthr` percentages into exact bpm corridors based on the athlete's stored LTHR in Intervals, and Garmin displays those raw calculated bpm corridors without clamping to watch zones.

## Colleague's note: What applied vs what was ignored

### What applied:
- **`start` vs `value` key name**: The observation that lower bound key `start` switches the FIT export mode from Lap-HR / zone-mapped (`{value, end}`) to an Instant-HR corridor (`{start, end}`), letting Garmin render the exact bpm corridor computed from Intervals' LTHR.
- **Units `%lthr`**: Maintaining `units: "%lthr"` with percentage values rather than absolute bpm or `start_bpm`/`end_bpm`, ensuring Intervals handles conversion from its stored LTHR.

### What was ignored:
- **Intervals text grammar and description generation**: The note discusses formatting the top-level `description` field for rendering in the Intervals web UI (e.g. grammar rules regarding `m` vs `mtr`, repeat blocks, and parser failure handling). Because `gen.py` directly targets the API `workout_doc.steps` structure which the API already accepts, web UI description generation was not part of the required fix.
- **External testing and reproduction steps**: Instructions regarding athlete authentication, API credentials, pushing events via `POST /api/v1/athlete/{id}/events`, and watch syncing were ignored per the ground rules to work only within the local workspace without communicating with external services.
