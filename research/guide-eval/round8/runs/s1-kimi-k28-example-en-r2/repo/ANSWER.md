# Fix: HR corridors clamped to the watch's own zones

## What changed

One word in `gen.py` (`hr_target`, line 13): the HR corridor's lower bound is
now `"start"` instead of `"value"`:

```python
# before
return {"units": "%lthr", "value": lo, "end": hi}
# after
return {"units": "%lthr", "start": lo, "end": hi}
```

## Why

Intervals' FIT export routes the HR target differently depending on the lower
bound's key name:

- `{units: "%lthr", value, end}` → exported as a **Lap-HR / zone-mapped**
  target. The watch resolves it against its own (auto-detected, stale) HR
  zones, which is why every corridor in `readback/watch-notes.md` landed on a
  watch zone edge (118–137, 151–162, 137–151) instead of the planned range.
  Changing the watch's LTHR moved the bands but they stayed zone edges.
- `{units: "%lthr", start, end}` → exported as an **Instant-HR corridor**. The
  watch displays the raw bpm Intervals computed from its own stored LTHR,
  immune to the watch's zones.

With the fix, the tempo-run plan should render on the watch as
117–129 / 151–160 / 129–141 / 112–124 bpm (percentages × Intervals LTHR 172),
matching the "expected" column in the watch notes.

## Colleague's note: what applied and what didn't

Applied:

- The core diagnosis and fix: `value` routes as zone-mapped Lap-HR, `start`
  makes it an Instant-HR corridor. The one-word rename, verified in their
  case with differing Intervals/watch LTHR (same situation as ours: 172 vs
  168).
- Corroboration of the earlier failed attempts: `units: "bpm"` with absolute
  values producing impossible 214–249 bpm readings, and `start_bpm`/`end_bpm`
  being silently dropped (constant 101 fallback) — identical to what's
  recorded in `readback/watch-notes.md`, so no need to retry those shapes.
- Keeping percentages (`%lthr`) rather than absolute bpm, so Intervals
  converts at export time from its own stored threshold.

Did not apply:

- The top-level `description` in Intervals' text grammar (`m` vs `mtr`,
  bare `Z2` = power, etc.). That trap makes steps invisible in the Intervals
  *web UI*; it was not our symptom. Our readback shows `workout_doc.steps`
  populated and the workout reaching the watch — only the corridor values
  were wrong. Adding a `description` field would be scope creep here.
- The note's step 1 prescription was already satisfied (we already send
  percentages, just under the wrong key name).
