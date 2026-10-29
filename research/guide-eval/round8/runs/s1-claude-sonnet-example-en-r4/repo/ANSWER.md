# Fix: HR corridors clamped to watch zones

**Change:** in `gen.py` `hr_target()` now emits `{"units": "%lthr", "start": lo, "end": hi}` instead of `{"units": "%lthr", "value": lo, "end": hi}`.

**Why:** `readback/watch-notes.md` shows every corridor snapping to the watch's zone bands (e.g. 75–82% planned as 129–141 showed 137–151). The API accepted the event, so the payload was valid but the wrong shape. With `value`, Intervals' FIT export produces a zone-mapped Lap-HR target, which the watch clamps to its own zones. With `start`, it produces an Instant-HR corridor with the raw bpm computed from Intervals' LTHR (172).

**Verification:** I only checked that the generated JSON now contains `start` for all 4 HR steps (the 3 steps plus the repeat's 2 inside). I did not push or test on a watch. Please push once and confirm the watch shows 117–129, 151–160, 129–141, 112–124.

**Colleague's note, what applied:**
- Applied: the `value` → `start` rename, and keeping `%lthr` percentages (already the case).
- Not applied: the `bpm` and `start_bpm`/`end_bpm` attempts (our notes show the same failures; we already avoid them).
- Not applied: the top-level `description` text grammar. Our symptom was watch values, not an invisible web-UI chart, and our readback has populated `steps`. It may be worth adding later if the UI shows only a name and duration.
