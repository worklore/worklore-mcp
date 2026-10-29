# Fix: HR ranges clamped to watch zones

**Changed:** `gen.py` `hr_target()` now emits `{"units": "%lthr", "start": lo, "end": hi}`
instead of `{"units": "%lthr", "value": lo, "end": hi}`.

**Why:** In the Intervals.icu workout_doc a range target is `start`/`end`; `value`
is the single-point form. We sent `value` + `end`, a mixed shape. The API accepted
it (steps populated), but the Garmin export apparently couldn't read it as a
custom range and fell back to the watch's zone band containing the target
(see `readback/watch-notes.md`). The earlier `start_bpm`/`end_bpm` attempt used
field names that don't exist, which explains the constant 101.

**Not verified:** I can't call the Intervals API or see the watch from here
(no external calls allowed), and this rests on my recollection of the schema.
Please push a test event and check the `GET` readback has `start`/`end` and the
watch shows 151–160 for Tempo. If it still snaps to zones, the next thing to
try is `units: "hr"`-style absolute bpm computed from LTHR 172 using the correct
`start`/`end` fields (the earlier bpm try used `value`, so it's not ruled out).
