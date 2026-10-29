# Fix: HR corridors clamped to the watch's zones

## What changed
`gen.py`, `hr_target()`: the lower bound is now emitted as `start` instead of
`value`: `{"units": "%lthr", "start": lo, "end": hi}`.

## Why
With `{value, end}` Intervals' FIT export builds a Lap-HR / zone-mapped target,
so the watch snaps it to its own zone bands. That matches `readback/watch-notes.md`:
every step showed a watch zone (118–137, 151–162, 137–151) instead of the planned
range, and setting the watch LTHR to 172 only moved the bands. With `{start, end}`
the export is an Instant-HR corridor, and the watch shows the bpm Intervals
computes (% × Intervals LTHR 172), e.g. Float 75–82% -> 129–141.

## Not verified
I did not push anything or look at a watch (no external calls allowed). The fix
is based on the colleague's note and the readback; the sent JSON had `value`, and
the next push needs checking: `GET /events/{id}` should show `start`/`end`, and
the watch should show 117–129 / 151–160 / 129–141 / 112–124.
The API readback may not confirm the export mode by itself, only the watch can.

## What from the colleague's note was useful
- Used: `start`/`end` instead of `value`/`end` (the actual fix).
- Used: keep `%lthr` percentages rather than absolute bpm. The code already did
  this, and the readme notes `bpm` / `start_bpm` / `end_bpm` were tried and failed.
- Used as a check: read the event back and confirm `workout_doc.steps` is non-empty.
- Skipped: the top-level `description` in Intervals' text grammar. It only fixes
  step visibility in the web UI, which isn't our problem, and a malformed
  description can wipe the workout, so I didn't add it untested. Worth a
  separate change if the UI chart is wanted.
- Skipped: the account/credential steps, creating test events, and the
  LTHR-mismatch diagnosis (already known here).
