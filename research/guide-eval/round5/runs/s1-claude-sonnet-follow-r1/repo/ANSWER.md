# HR corridor fix

**Cause:** `gen.py` emitted HR targets as `{"units": "%lthr", "value": lo, "end": hi}`. In Intervals' FIT export, `value`+`end` is routed as a Lap-HR / zone-mapped target, so the watch clamped each corridor to its own zones (the pattern in `readback/watch-notes.md`). The API accepts it either way, which is why the readback looked fine.

**Changes (`gen.py`):**
- `hr_target` now emits `{"units": "%lthr", "start": lo, "end": hi}`. `start` makes it an Instant-HR corridor, so the watch shows the raw bpm Intervals computes from its stored LTHR (172 x 75-82% = 129-141). Still percentages, not absolute bpm.
- The event now also carries a top-level `description` in Intervals' text grammar (`- Warm-up easy 10m 68-75% LTHR`, with blank lines around `3x` repeat blocks). Without it the web UI doesn't show the steps. It uses `m` for minutes, rejects labels starting with a digit, and uses no bare `Z<n>`.

**Not verified:** I couldn't push or sync a watch. The `start`/`end` shape and the description grammar come from the guide, not a live test. Re-push the event, read it back (`workout_doc.steps` must be non-empty; `[]` means the description failed to parse), then check the watch shows 117-129 / 151-160 / 129-141 / 112-124. Delete the old event 184233 first.
