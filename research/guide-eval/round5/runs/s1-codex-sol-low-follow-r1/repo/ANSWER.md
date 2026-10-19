# Generator fix

Changed `gen.py` so each HR target uses `{"units": "%lthr", "start": low, "end": high}`. Intervals treats `value`/`end` as a zone-mapped Lap-HR target, which explains the watch's zone-edge ranges in `readback/watch-notes.md`. `start`/`end` requests the Instant-HR corridor, preserving the planned percentage bounds when Intervals exports them using its stored LTHR.

The generated event also includes a top-level `description` in Intervals' workout text grammar. It uses minute durations, explicit `% LTHR` targets, and blank lines around the `3x` repeat block so the steps can appear in the web UI and survive description parsing.

Verified locally with `python3 gen.py plans/tempo-run.json`: all four HR steps have `start`/`end` targets, and the description contains the warm-up, repeat block, and cool-down. A Garmin display check requires a later API push, readback, and watch sync; none were performed here.
