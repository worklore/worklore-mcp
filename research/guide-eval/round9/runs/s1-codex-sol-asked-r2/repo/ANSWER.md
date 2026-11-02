# HR range fix

Changed `gen.py` to write each heart-rate corridor as `hr: {"units": "%lthr", "start": lo, "end": hi}`. The old output used `value` for the lower bound. In Intervals.icu's [workout document format](https://forum.intervals.icu/t/downloading-planned-workouts-from-the-api/93737), `value` is a single target, while `start` and `end` define a range. That explains why the watch received zone-shaped targets instead of the planned corridors: the lower bound was treated as a single target and the `end` field did not form a valid range with it.

The plan percentages and LTHR-based conversion remain the same. With LTHR 172, the intended corridors are approximately 117–129, 151–160, 129–141, and 112–124 bpm for warm-up, tempo, float, and cool-down. The generator now sends both bounds for every step, including steps inside repeats.

Added `test_gen.py` to check all four corridors in the generated workout document. `python3 -m unittest -v test_gen` passes, and `python3 gen.py plans/tempo-run.json` produces `start`/`end` pairs throughout. No event was pushed, so the Garmin display has not been verified with this revision.
