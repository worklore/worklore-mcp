# HR range fix

Changed `hr_target` in `gen.py` to emit `{"units": "%lthr", "start": lo, "end": hi}` instead of using `value` for the lower bound.

For Intervals' Garmin FIT export, `value`/`end` selects a lap-HR, zone-mapped target, so the watch replaces the planned corridor with its own zone edges. `start`/`end` selects an instant-HR corridor, preserving the BPM range that Intervals calculates from its stored LTHR. The values remain percentages; converting them to absolute BPM in the generator would risk the double conversion seen in the earlier attempt.

Verified locally by running `python3 gen.py plans/tempo-run.json` and checking all four HR targets: warm-up `68–75`, tempo `88–93`, float `75–82`, and cool-down `65–72`, all with `start`/`end` and no `value` key. No event was deployed or synced, so watch behavior was not retested.

Source for the `start`/`end` export behavior: [Exact HR corridors on Garmin from Intervals.icu API workouts](https://worklore.dev/s/2026-05-12-exact-hr-corridors-on-garmin-from-intervals-icu-api-workouts).
