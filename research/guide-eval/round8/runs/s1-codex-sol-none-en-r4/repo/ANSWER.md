# HR range fix

Changed `gen.py` to write each HR corridor as `hr: {"units": "%lthr", "start": low, "end": high}`. Intervals.icu's `workout_doc` uses `value` for one target and `start`/`end` for a range. The old generator combined `value` with `end`, so it did not express the planned corridor as a proper range. The watch readback showed zone boundaries instead of the planned limits.

The plan remains in percent of LTHR, so Intervals can resolve it using the athlete's threshold. With LTHR 172, the plan's approximate corridors are 117–129, 151–160, 129–141, and 112–124 bpm for warm-up, tempo, float, and cool-down respectively. No event was sent to Intervals or Garmin; watch behavior still needs a fresh sync to confirm.

Verified locally by generating `plans/tempo-run.json` and checking all four HR targets, including both steps inside the repeat block, contain `start` and `end` and no `value`.
