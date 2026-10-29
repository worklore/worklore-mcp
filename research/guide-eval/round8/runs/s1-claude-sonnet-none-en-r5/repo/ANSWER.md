# Change

`gen.py` `hr_target()` emitted a range as `{"units": "%lthr", "value": lo, "end": hi}`.
It now emits `{"units": "%lthr", "start": lo, "end": hi}`.

# Why (a hypothesis, not verified)

As I understand the Intervals.icu workout_doc format, a target is either a single
`value` or a range given as `start` + `end`. We mixed `value` with `end`, which is
neither form. The API still accepted it, and `workout_doc.steps` came back populated.
The range then likely lost its `end` on export. The watch would fall back to a plain
zone target, which matches the zone bands it showed.

The earlier attempts in the notes (`units: "bpm"`, `start_bpm`/`end_bpm`) used
different keys or units. As far as the notes show, `start`/`end` with `%lthr` was never tried.

# Not tested

I can't reach Intervals or the watch from here and didn't push anything. I only checked
that the generated JSON now has `start`/`end`. To confirm, regenerate and push, read the
event back, and check the watch. Expected: Tempo 151–160, Float 129–141.

If the watch still shows zone bands, the cause is probably on the Intervals→Garmin export
side. That would need a check of how Intervals exports `%lthr` HR targets. Absolute bpm
may be needed, with the correct `units` string for it.

The checked-in `readback/event-184233-as-sent.json` is a record of the old output, so I left it alone.
