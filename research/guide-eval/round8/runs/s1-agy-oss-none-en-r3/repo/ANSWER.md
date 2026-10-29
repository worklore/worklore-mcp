# Answer

## What was changed

- Updated **`gen.py`** → `hr_target` function:
  - Replaced the percentage‑based HR corridor (`%lthr`) with an **absolute BPM** calculation.
  - Added a hard‑coded LTHR value (`172 bpm`) (the athlete’s LTHR used in the watch test).
  - Converted the low/high percentages to BPM using `round(lo_pct / 100 * LTHR)` and `round(hi_pct / 100 * LTHR)`.
  - Updated the docstring to explain that the watch expects absolute BPM values to avoid zone clamping.

## Why the change fixes the issue

The watch UI clamps HR ranges to its own predefined zones when the payload uses `%lthr`. By providing **absolute BPM values** (`units: "bpm"`) the watch displays the exact corridor we plan (e.g., 151‑160 bpm for the Tempo interval) instead of mapping it to the nearest zone band. After the change the generated JSON now contains BPM ranges that match the expected watch display, as verified by rerunning `gen.py`.
