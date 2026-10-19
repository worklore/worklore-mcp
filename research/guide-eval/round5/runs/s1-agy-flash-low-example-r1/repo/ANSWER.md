# Changes to Workout Generator

## What Changed
In `gen.py`, updated the dictionary returned by `hr_target(step)`:
- Changed the lower-bound key name from `"value"` to `"start"`.
- The target dictionary is now `{"units": "%lthr", "start": lo, "end": hi}` instead of `{"units": "%lthr", "value": lo, "end": hi}`.

## Why
When Intervals.icu exports workouts to Garmin FIT format:
- A target defined with `{"value": ..., "end": ...}` is treated as a Lap-HR / zone-mapped target, causing Garmin watches to clamp the corridor to the watch's own locally configured heart rate zones rather than using the target range.
- A target defined with `{"start": ..., "end": ...}` routes as an Instant-HR corridor. In this mode, Intervals computes the raw bpm values from its stored athlete threshold (`%lthr`) and exports an exact bpm corridor to the watch, avoiding watch-side zone clamping and drift.

## Colleague's Note: What Applied vs. What Was Ignored

### Applied
- **Renaming the lower-bound target key (`value` -> `start`)**: Changing the target schema from `{"units": "%lthr", "value": ..., "end": ...}` to `{"units": "%lthr", "start": ..., "end": ...}` was the exact fix required to switch Intervals from generating a Lap-HR zone-mapped target to an Instant-HR target corridor.
- **Keeping percentage units (`%lthr`)**: Confirmed that `units: "%lthr"` should be preserved rather than attempting absolute bpm or other unit forms (`start_bpm`/`end_bpm`), letting Intervals do the conversion from its athlete thresholds at export time.

### Ignored
- **Intervals text grammar and top-level `description` parsing**: The note discussed formatting rules for Intervals' plain-text description grammar (e.g. `m` vs `mtr`, repeat blocks, UI step rendering). The generator creates structured JSON via `workout_doc` without generating a top-level text `description`, and the API already accepts `workout_doc.steps` directly without parser choke.
- **Garmin Connect / Intervals API sync instructions**: Step-by-step instructions for creating test events, interacting with the Intervals.icu API endpoints, and syncing to a physical watch were ignored per the ground rules to work strictly locally.
