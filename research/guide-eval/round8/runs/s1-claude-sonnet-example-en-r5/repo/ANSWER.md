# Fix: HR corridors clamped to watch zones

**Cause:** `gen.py` `hr_target()` emitted `{"units": "%lthr", "value": lo, "end": hi}`. With `value` as the lower bound, Intervals' FIT export produces a zone-mapped Lap-HR target, so the watch snaps it to its own zone bands. That matches `readback/watch-notes.md`: the API accepted the event, but the watch showed zone edges (118–137, 151–162, 137–151).

**Change:** `gen.py` now emits `{"units": "%lthr", "start": lo, "end": hi}`. `start` makes Intervals export an Instant-HR corridor, so the watch shows the bpm Intervals computed from its own LTHR (172). Expected: 129–141 for the Float step, 151–160 for Tempo.

**Not verified:** I haven't pushed anything or checked a watch. Nothing here can reach Intervals or a Garmin. Please push a test event and compare against the table in the notes.

## Colleague's note
- Applied: the `value` → `start` rename, and keeping `%lthr` percentages rather than absolute bpm. The plan already used percentages, so that part needed no change.
- Not applied: the top-level `description` text grammar. It only affects how the Intervals web UI draws the steps. Your symptom is on the watch, and the readback shows `workout_doc.steps` is populated. If the web UI shows only a name and total duration, that would be a separate change.
- Not applicable: the `bpm` and `start_bpm` attempts. Your notes show you already tried them and they failed.
