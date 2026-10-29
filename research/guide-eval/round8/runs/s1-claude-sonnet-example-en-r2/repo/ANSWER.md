# Fix: HR corridors clamped to the watch's zones

**Change:** `gen.py` `hr_target()` now emits `{"units": "%lthr", "start": lo, "end": hi}` instead of `{"units": "%lthr", "value": lo, "end": hi}`.

**Why:** `readback/event-184233-as-sent.json` shows we sent `value`+`end`. The API accepts that, but the FIT export treats it as a zone-mapped Lap-HR target, so the watch snapped each range to its own zone band (e.g. 129–141 shown as 137–151). That matches `readback/watch-notes.md`. A `start`+`end` pair exports as an Instant-HR corridor, which the watch shows as the raw bpm Intervals computes (% × Intervals LTHR 172). Percentages stay the unit.

**Colleague's note:**
- Applied: the `value` -> `start` rename, and keeping `%lthr` rather than bpm. Our notes show the same failed `bpm` and `start_bpm`/`end_bpm` attempts, so I didn't retry them.
- Not applied: the top-level `description` text grammar advice. Our steps already read back populated and no web UI problem was reported, so I left it alone.

**Not verified:** I couldn't push or sync to a watch here. Please push a new event and check that the Tempo step reads about 151–160 bpm. Also re-read the event via the API to confirm `steps` is still populated.
