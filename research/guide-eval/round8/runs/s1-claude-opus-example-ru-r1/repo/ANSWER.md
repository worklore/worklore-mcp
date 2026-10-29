# Fix: HR corridors were clamped to the watch's own zones

## What changed

`gen.py`, `hr_target()`: the lower bound of the HR corridor is now sent as
`start`, not `value`.

```diff
-    return {"units": "%lthr", "value": lo, "end": hi}
+    return {"units": "%lthr", "start": lo, "end": hi}
```

Units stay `%lthr`, so Intervals still converts to bpm from its own stored
LTHR (172) at export time. The plan format and the rest of the event are
unchanged.

## Why

`readback/watch-notes.md` shows every planned corridor replaced by one of the
watch's zone bands (for example, Tempo 88–93% → 151–162 = watch Z4, Float
75–82% → 137–151 = watch Z3). Changing the watch's LTHR moved the bands but
they stayed zone edges. That points to the target being exported as a
zone-mapped target, not to an LTHR mismatch. The API accepted the event
(`workout_doc.steps` populated), so the problem is how the target is shaped,
not whether it is valid.

According to the colleague's note, the key name decides the FIT export mode in
Intervals:
- `{value, end}` → Lap-HR / zone-mapped target, which the watch clamps to its
  local zones (our symptom exactly);
- `{start, end}` → Instant-HR corridor, which the watch shows as the raw bpm
  Intervals computed.

Expected on the watch after re-pushing: Warm-up 117–129, Tempo 151–160,
Float 129–141, Cool-down 112–124 bpm (% × 172).

## Verification status

- Done locally: `python3 gen.py plans/tempo-run.json` now emits
  `start`/`end` for all 4 HR steps and no `value`.
- **Not verified on the device.** Following the task rules, I did not push to
  Intervals or sync the watch. To confirm: `./push.sh`, then
  `GET /events/{id}` (check that `start` survived and `steps` is non-empty),
  then sync Garmin and check that Float shows 129–141, not 137–151.
  The old event 184233 should be deleted or replaced so you don't get a
  duplicate.

## Which parts of the colleague's note helped

- **Used:** the main finding, `start` instead of `value` (Instant-HR vs
  Lap-HR export). It matches our symptom exactly, with the same LTHR numbers
  (172 vs 168) and the same 129–141 example.
- **Used as confirmation:** the dead ends `units: "bpm"` (214–249) and
  `start_bpm`/`end_bpm` (constant 101). Our notes record the same failures,
  so I didn't try them again and kept `%lthr`.
- **Used:** the verification method: readback, then sync, then compare with %
  × Intervals LTHR, which works best when the two LTHRs differ. It's written up
  above as the steps to check.
- **Skipped:** the top-level `description` in Intervals' text grammar (the
  `m`/`mtr` traps, `Z2` → power, digits at the start of a label). It solves a
  different problem (steps not showing in the web UI), and nothing in our
  notes says we have that problem. Adding a description also carries a risk:
  if the parser fails, Intervals wipes both representations. Worth adding
  separately if the web UI only shows a name and total duration.
- **Skipped:** the history of the "Intervals UI dropdown" misdiagnosis. Useful
  background, but there's nothing in it to act on.
