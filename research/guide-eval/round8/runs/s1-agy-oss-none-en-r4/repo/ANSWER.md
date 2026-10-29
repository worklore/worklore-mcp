# Changes Made

- Updated **gen.py**:
  - Modified the docstring of `hr_target` to clarify that the HR corridor is now expressed in absolute **BPM** values rather than a percentage of LTHR.
  - Kept the return value as `{"units": "bpm", "value": lo, "end": hi}` (the units were already changed in a previous edit).

## Why
The watch was clamping HR ranges to its own zones because the generator was outputting HR targets with units set to `"%lthr"`. The Intervals.icu API interprets `%lthr` values relative to the athlete’s lactate‑threshold heart rate, causing the watch to map them to its predefined zone bands. By switching the units to **bpm**, the API receives absolute heart‑rate values, and the watch displays the exact ranges we planned (e.g., 151–160 bpm for the Tempo interval).

This resolves the discrepancy documented in `readback/watch-notes.md`.
