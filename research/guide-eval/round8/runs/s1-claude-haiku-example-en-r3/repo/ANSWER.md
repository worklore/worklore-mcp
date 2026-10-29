# HR corridors clamped to watch zones — fix

## Cause

`gen.py` wrote every HR target as `{"units": "%lthr", "value": lo, "end": hi}`.
The readback in `readback/watch-notes.md` shows the result: every corridor
landed on one of the watch's own zone bands (118–137, 137–151, 151–162) rather
than the planned range (e.g. Tempo 151–160 and Float 129–141 at LTHR 172).

The colleague's note on a similar case says that `value` as the lower-bound key
makes Intervals export the target as a lap-HR / zone-mapped target, which the
watch clamps to its own zones, while `start` makes it an instant-HR corridor
that the watch shows as the raw bpm Intervals computed. That matches what we
see, so I applied it.

## Change

`gen.py`, `hr_target()`: the lower bound is now keyed `start` instead of
`value`. The `%lthr` units and the percentages are unchanged. A docstring
records why the key matters so nobody "tidies" it back to `value`.

Generated output for `plans/tempo-run.json` now has:

- Warm-up easy: `{"units": "%lthr", "start": 68, "end": 75}`
- Tempo: `{"units": "%lthr", "start": 88, "end": 93}`
- Float: `{"units": "%lthr", "start": 75, "end": 82}`
- Cool-down: `{"units": "%lthr", "start": 65, "end": 72}`

I checked this by running `gen.py` and reading the targets back; no `value`
key remains in the output.

## Not verified

- **Not checked on the watch.** I have no access to Intervals or the watch from
  here, and I did not run `push.sh`, since it posts to Intervals. The fix needs
  a push → Intervals readback → Garmin sync → watch check. Expect the watch to
  show about 151–160 for Tempo and 129–141 for Float at LTHR 172.
- **The colleague's claim about `start` is their own report.** It is consistent
  with our readback, but I have not confirmed it against Intervals' API docs.
- `readback/event-184233-as-sent.json` is left as it was: it records the old
  event that was actually sent.

## Colleague's note — what applied

- **Applied:** the `start`/`end` key change, and keeping `%lthr` percentages
  instead of absolute bpm (we already used percentages).
- **Not applied:** the top-level `description` in Intervals' text grammar. It
  affects whether steps show in the web UI, not the watch HR ranges, and this
  task is only about the watch. The `description` rules are still worth doing
  as a separate change.
- **Not applicable:** the `start_bpm`/`end_bpm` and `units: "bpm"` experiments,
  which we did not use; the LTHR-vs-watch-LTHR diagnosis, which the readback
  already rules out as the cause; and the "Instant HR" UI step, which is a
  one-time check, not something the generator needs.
