# Change Summary

## What was changed
- Updated **`gen.py`** `hr_target` function:
  - Added documentation explaining the inclusion of absolute BPM values.
  - Introduced a default LTHR of **172** (the athlete’s current threshold).
  - Calculated `start_bpm` and `end_bpm` from the percentage range.
  - Returned a dictionary with **`units: "bpm"`**, `value` (start BPM) and `end` (end BPM) instead of the previous `%lthr` representation.

## Why the change was needed
The watch displayed HR ranges clamped to its own zone bands because the generated workout JSON used `%lthr` units. Intervals.icu interprets `%lthr` ranges as zone edges, causing the watch to map each corridor to the nearest zone. By emitting absolute BPM values (`units: "bpm"`) the watch can display the exact heart‑rate corridor we planned (e.g., 151‑160 bpm for the Tempo interval), matching the plan’s intended percentages.

## Result
Running `python3 gen.py plans/tempo-run.json` now produces a `workout_doc` where each step’s `hr` field looks like:
```json
"hr": {"units": "bpm", "value": 151, "end": 160}
```
which aligns with the expected watch display as shown in `readback/watch-notes.md`.

*All changes are confined to the current workspace (`/tmp/h-2blV9n`). No deployment or external actions were performed.*