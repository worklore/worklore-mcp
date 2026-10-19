# HR corridors clamped to watch zones

**Change:** in `gen.py`, `hr_target()` now emits `{"units": "%lthr", "start": lo, "end": hi}` instead of `{"units": "%lthr", "value": lo, "end": hi}`.

**Why:** `readback/watch-notes.md` shows the API accepted the event and returned it exactly as sent, so the problem is in how Intervals exports it. The note in `notes/exact-hr-corridors-on-garmin-from-intervals-icu-api-workouts.md` reports that a `value`/`end` target is exported as a zone-mapped (Lap-HR) target, which the watch clamps to its own zones. That matches what we saw: every step showed a watch zone band. A `start`/`end` target is exported as an Instant-HR corridor, so the watch shows the bpm range Intervals computed (% of Intervals' LTHR 172). The `bpm` and `start_bpm`/`end_bpm` attempts in the watch notes were dead ends and are not used.

**Not verified:** I can't push or sync a watch from here (no deploying or submitting). I only checked that `gen.py` now emits `start` for every HR step. The note's account of how the export works comes from a forum-style write-up, not from Intervals' docs. Please push the regenerated event and confirm the watch shows 117–129, 151–160, 129–141 and 112–124 bpm.

**Not changed:** that note also says steps may not show in the Intervals web UI unless the event has a top-level `description` in Intervals' text grammar. That is separate from this bug, so I left it alone.
