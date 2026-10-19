# Fix: HR corridors clamped to the watch's zones

**Cause:** `gen.py` `hr_target()` emitted `{"units": "%lthr", "value": lo, "end": hi}`. In Intervals' FIT export, `value`+`end` becomes a zone-mapped Lap-HR target, so the watch snaps it to its own zone bands (matches `readback/watch-notes.md`: every step showed a watch zone edge, e.g. 137–151 instead of 129–141, and changing the watch LTHR only moved the bands).

**Change:** `hr_target()` now emits `{"units": "%lthr", "start": lo, "end": hi}`. The lower-bound key `start` makes the export an Instant-HR corridor, so the watch shows bpm computed by Intervals (% × LTHR 172), independent of the watch's LTHR. Added a docstring explaining this. Nothing else in `gen.py` changed; the percentages and units are the same.

**Not verified:** I couldn't push to Intervals or sync a watch (no credentials, and told not to contact external services). Expected on the watch after re-pushing: 117–129, 151–160, 129–141, 112–124 bpm. Please check Float shows 129–141 on the watch.

**Colleague's note — what applied:**
- Applied: the `start`/`end` vs `value`/`end` finding, and keeping `%lthr` percentages rather than absolute bpm (already our approach).
- Already consistent with our earlier failed attempts (`bpm` units → 214–249; `start_bpm` → 101).
- Not applied: the top-level `description` text grammar. Our problem was the watch values, not the web UI rendering, and I can't test the parser here; adding it risks Intervals wiping the steps. Worth considering only if the UI shows no step chart.
- `readback/event-184233-as-sent.json` is left untouched: it records what was sent (with `value`), so it's the evidence of the bug. Re-read the live event after re-pushing to confirm `start` is kept.
