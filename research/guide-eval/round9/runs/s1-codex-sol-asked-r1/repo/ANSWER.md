# HR range generator fix

Changed `gen.py` to emit HR corridors as `hr: {"units": "%lthr", "start": low, "end": high}`. Intervals.icu uses `value` for a single target and `start`/`end` for a range. The old `value`/`end` combination did not encode the planned corridor, which explains why the watch showed zone bands instead of the requested bounds. The [Intervals.icu workout builder example](https://forum.intervals.icu/t/workout-builder/1163?page=55) shows this exact `%lthr` range shape.

Kept the plan's percentages of LTHR so Intervals.icu can resolve them against its 172 bpm threshold; the watch's auto-detected 168 bpm threshold should not redefine the planned bounds. This avoids the earlier malformed absolute-bpm and `start_bpm`/`end_bpm` attempts recorded in `readback/watch-notes.md`.

Added `test_gen.py` to check every corridor, including both steps inside the repeat block. `python3 -m unittest -v test_gen.py` passes, and the generated JSON now contains the four intended `start`/`end` pairs. Watch behavior still needs a future sync/readback to confirm; no event was sent as part of this change.
