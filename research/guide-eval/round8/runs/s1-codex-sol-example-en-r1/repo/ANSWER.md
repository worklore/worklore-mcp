# HR corridor fix

Changed `gen.py` to emit HR targets as `{"units": "%lthr", "start": low, "end": high}`. The previous `value` lower bound produced watch targets at its local HR zone edges, as recorded in `readback/watch-notes.md`. Using `start` selects the instant HR corridor described in the colleague's note, while keeping percentages tied to the LTHR stored in Intervals.

The note's `start`/`end` finding applies to this case. Its advice to keep `%lthr` also applies and was already implemented. The `bpm` and `start_bpm`/`end_bpm` failed attempts agree with the readback, so neither shape was used. The top-level `description` grammar and parser issue do not apply to this fix: the saved event already has populated `workout_doc.steps`, and the reported problem is the watch's HR targets.

Verified locally that the generated workout uses `start`/`end` for every HR step, including repeated steps, and contains no `value` HR key. No event was posted or watch-synced, so the watch result still needs an end-to-end check when the next workout is sent.
