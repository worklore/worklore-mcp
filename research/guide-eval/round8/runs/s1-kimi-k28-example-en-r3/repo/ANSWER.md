# Fix: HR corridors clamped to watch zones

## What changed

`gen.py`, `hr_target()` — one key renamed in the HR target object:

```json
{"units": "%lthr", "value": lo, "end": hi}   →   {"units": "%lthr", "start": lo, "end": hi}
```

## Why

The watch notes show the exact signature of zone-mapped export: every planned
corridor (`plans/tempo-run.json`, % of LTHR) showed up on the watch as one of
the Forerunner's own zone bands — 118–137 (watch Z2) instead of 117–129,
151–162 (watch Z4) instead of 151–160, 137–151 (watch Z3) instead of 129–141.
Changing the watch's LTHR moved the bands but never produced the planned
edges, which means the watch never received a real corridor at all — it
received a zone-style target and clamped it.

Per the colleague's investigation, the lower-bound key name selects the
Intervals FIT-export mode: `{value, end}` routes as a **Lap-HR / zone-mapped**
target (watch clamps to its local zones, drift-prone), while `{start, end}`
routes as an **Instant-HR corridor**, so the watch displays the raw bpm
Intervals computed from its own stored LTHR (172). That makes the planned
values render exactly: warm-up 117–129, tempo 151–160, float 129–141,
cool-down 112–124 — drift-immune regardless of the watch's auto-detected
LTHR. Notably, the float step (75–82% × 172 = 129–141) is the identical
corridor the colleague verified end-to-end, which cross-checks the diagnosis.

Keeping `%lthr` units (rather than absolute bpm) is deliberate: it matches the
verified-working shape, and Intervals converts to bpm at export time from its
own threshold.

## Verification

Regenerated `python3 gen.py plans/tempo-run.json` and diffed against
`readback/event-184233-as-sent.json`: the only difference across all four HR
targets is `value` → `start`. Units, bounds, durations, labels, and the repeat
block are unchanged. Not re-pushed to the API per the ground rules — next
push/sync should show the raw bpm corridors above.

## Colleague's note — what applied, what didn't

Applied:

- **`start` vs `value` as the lower-bound key** — the core fix; one-word
  rename switches the FIT export from zone-mapped to instant-HR corridor.
- **The "absolute bpm is impossible" conclusion being wrong** — explains why
  the generator already uses `%lthr` percentages instead of bpm, which was
  correct to keep.
- **The failed-attempt history** (`units: "bpm"` → watch showed 214–249;
  `start_bpm`/`end_bpm` → constant 101) matches our `readback/watch-notes.md`
  exactly, confirming this is the same failure mode.

Did not apply:

- **The top-level `description` / text-grammar trap** (`m` = minutes, `mtr`/
  `km` for distance, bare `Z2` = power zones, etc.). That fixes steps being
  invisible in the Intervals *web UI* — a symptom we don't have: the API
  readback shows `workout_doc.steps` populated and the notes only report wrong
  HR bands on the watch. Adding a `description` field would be an unrelated
  change, so it was left out.
