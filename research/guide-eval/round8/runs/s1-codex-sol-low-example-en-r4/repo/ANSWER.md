# HR corridor fix

Changed `gen.py` so percentage-of-LTHR HR corridors use `start` and `end`, rather than `value` and `end`. The previous event readback preserved `value`/`end`, while the watch displayed its own zone boundaries instead of the planned ranges. The colleague's finding that `start`/`end` selects an instant HR corridor directly applies to this symptom. The generator still uses `%lthr`, letting Intervals calculate bpm from its stored LTHR of 172.

Verified the sample plan generates all four expected `start`/`end` targets, including those inside the repeat block. This is a local payload check; no new Intervals or Garmin round trip was performed.

The colleague's warnings about absolute `bpm` and `start_bpm`/`end_bpm` agree with the failed attempts in `readback/watch-notes.md`, so neither format was used. The top-level `description` parser advice was not applied: the recorded API readback already has populated `workout_doc.steps`, and the reported problem is the watch's HR ranges, not missing steps in the Intervals UI.
