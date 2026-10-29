# HR corridors clamped to the watch's zones — fix

## What changed

`gen.py`, `hr_target()`: the corridor's lower bound is now `start` instead of
`value`.

```diff
-    return {"units": "%lthr", "value": lo, "end": hi}
+    return {"units": "%lthr", "start": lo, "end": hi}
```

A docstring next to it explains why. Nothing else changed. Units stay
`%lthr`, so Intervals still converts to bpm from its own stored LTHR (172)
when it exports the FIT file.

## Why

When a target is `{value, end}`, Intervals' FIT export sends it as a
zone-mapped (Lap HR) target. The watch then snaps it to its own HR zone bands.
`readback/watch-notes.md` shows exactly that. Every displayed range is one of
the Forerunner's zones (118–137, 151–162, 137–151), never the planned range.
Changing the watch LTHR moved the bands but they stayed zone edges.

When a target is `{start, end}`, it is exported as an Instant-HR corridor in
the raw bpm Intervals computed. With LTHR 172 the watch should show:

| step | % LTHR | expected bpm |
|---|---|---|
| Warm-up easy | 68–75 | 117–129 |
| Tempo | 88–93 | 151–160 |
| Float | 75–82 | 129–141 |
| Cool-down | 65–72 | 112–124 |

**Status: I only checked this locally.** I regenerated
`plans/tempo-run.json`, and every `hr` target now has `start`/`end` and no
`value`. I did not push the event, read it back from the API, or sync a watch.
To confirm, run `./push.sh`, then `GET /events/{id}` and check that the `hr`
targets kept `start`, then sync and check that the watch shows the bpm in the
table above. Your Intervals LTHR (172) and the watch's (168) differ, so if the
watch shows those numbers, it is using Intervals' values and not its own.

## Which parts of the colleague's note applied

- **Applied: the main finding (`start` vs `value`).** Our symptom is the same
  one: ranges clamped to the watch's local zones. Our event used
  `{units: "%lthr", value, end}`, the exact shape the note says gets
  zone-mapped.
- **Applied: keep percentages, don't use absolute bpm.** We already used
  `%lthr`. Our notes record the same failed attempts as the note (`units:
  "bpm"` → 214–249 bpm, `start_bpm`/`end_bpm` → constant 101), so I didn't
  try those again.
- **Applied as a check only: the readback step.** Our readback already has
  `workout_doc.steps` populated, so the API accepts the structure. After the
  next push, check again that `start` is still there.
- **Not applied: the top-level `description` / text-grammar part.** That
  section fixes a different problem: steps not showing in the Intervals web
  UI. Our notes don't report that problem, and it has nothing to do with HR
  clamping. The note also warns that a description the parser can't read
  makes Intervals wipe both representations. That makes it a risky addition
  that isn't needed for this fix. If the web UI turns out to show only a name
  and duration, that section is the place to start (watch for `m` meaning
  minutes, distance in `mtr`/`km`, no digits at the start of labels).
- **Not applied:** the Garmin/Intervals account setup and the instruction to
  create and delete a test event. I didn't contact any external service.
