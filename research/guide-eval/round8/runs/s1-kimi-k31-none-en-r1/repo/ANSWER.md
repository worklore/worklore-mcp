# HR range fix

The generator was sending `hr` targets in `%lthr` units and leaving the BPM conversion to the export path. On the watch, those targets were mapped to its own heart-rate zones, so only the zone boundaries were displayed.

Changes:

- `gen.py` now converts both ends of each `hr_pct` range to absolute BPM with `round(percent * lthr / 100)` and emits the standard `hr` range object as `{"units": "bpm", "value": ..., "end": ...}`.
- The plan's LTHR is passed through both ordinary steps and steps nested in repeat blocks.
- `plans/tempo-run.json` now records the athlete's LTHR as `"lthr": 172`.
- `README.md` now describes the explicit BPM conversion.

Verification: running `python3 gen.py plans/tempo-run.json` produces HR ranges of 117–129, 151–160, 129–141, and 112–124 BPM, matching the expected values in `readback/watch-notes.md`. The repeat count and all step durations were also checked. Nothing was deployed or sent to an external service; watch behavior still needs an on-device check after the next manually initiated sync.
