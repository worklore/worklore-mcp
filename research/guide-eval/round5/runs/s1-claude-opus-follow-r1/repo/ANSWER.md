# Fix: HR corridors clamped to the watch's zones

## Cause

`gen.py` wrote each HR target as `{"units": "%lthr", "value": lo, "end": hi}`.
Intervals accepts that shape, and the readback looks fine. But when it builds
the FIT file, `{value, end}` becomes a **Lap-HR / zone-mapped** target, so the
watch snaps it to its own HR zone bands (built from its auto-detected LTHR of 168).
That matches every row in `readback/watch-notes.md`: the watch displayed one of its
own zones (118–137, 151–162, 137–151) and never the planned range. Changing the
watch's LTHR moved the bands, but they were still zone edges.

The earlier tries failed for different reasons. Absolute `bpm` gets misread at
export (the watch showed 214–249). `start_bpm`/`end_bpm` aren't part of the schema
and get dropped silently (constant 101 is Garmin's "no valid target" fallback).

## Change (`gen.py`)

1. **`hr_target`: the lower bound is now `start` instead of `value`.**
   `{"units": "%lthr", "start": lo, "end": hi}` exports as an **Instant-HR
   corridor**. The watch then shows the raw bpm that Intervals computed from its
   own LTHR (172) and ignores the watch's zones. Targets stay as percentages,
   so Intervals does the conversion at export from the threshold it has stored.
   This rename is the actual fix.
2. **The event now gets a top-level `description`** in Intervals' text
   grammar, so the steps show in the Intervals web UI (the UI reads
   `description`, not `workout_doc`). For the tempo plan:

   ```
   - Warm-up easy 10m 68-75% LTHR

   3x
   - Tempo 8m 88-93% LTHR
   - Float 2m 75-82% LTHR

   - Cool-down 5m 65-72% LTHR
   ```

   It follows the grammar rules: `m` means minutes and is used only for
   durations (non-whole minutes become `s`). There are blank lines around `Nx`
   repeat blocks and targets are explicit `% LTHR`, never a bare `Z<n>`. A label
   that starts with a digit raises an error instead of being sent, because the
   parser would read the digit as a duration, and a description it can't parse
   makes Intervals wipe both representations.

## Expected on the watch (LTHR 172 in Intervals)

| step | % LTHR | bpm |
|---|---|---|
| Warm-up easy | 68–75 | 117–129 |
| Tempo | 88–93 | 151–160 |
| Float | 75–82 | 129–141 |
| Cool-down | 65–72 | 112–124 |

## Not done here (needs your account and watch)

Following the ground rules, I didn't push anything. To verify:

1. `python3 gen.py plans/tempo-run.json > event.json && ./push.sh event.json`
2. `GET /api/v1/athlete/{id}/events/{new id}`: `workout_doc.steps` should be
   non-empty with `start`/`end` in the HR targets. If you get `steps: []`, the
   description parser choked.
3. Sync through Garmin Connect and open the workout. The watch should show the
   bpm values in the table above. Because the watch's LTHR (168) differs from
   Intervals' (172), this proves the targets come from Intervals.
4. Delete the old event 184233 (and the test event, if you want).
