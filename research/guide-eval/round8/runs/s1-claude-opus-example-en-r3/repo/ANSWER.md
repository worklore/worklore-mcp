# HR corridors clamped to watch zones — fix

## What changed

`gen.py`, `hr_target()`: the HR target's lower bound is now `start`
instead of `value`. The function now returns this:

```json
{"units": "%lthr", "start": 68, "end": 75}
```

It used to return `{"units": "%lthr", "value": 68, "end": 75}`. I didn't
change anything else.

## Why

Intervals.icu decides how to export an HR target to FIT from the key name.
`{value, end}` goes out as a zone-mapped target, and the watch replaces it
with whichever of its own HR zones fits. `readback/watch-notes.md` shows
exactly this: every step appeared as a band of the watch's zones (118–137,
151–162, 137–151), based on the watch's LTHR of 168. When the LTHR on the
watch was changed, the bands moved with it. `{start, end}` goes out as an
exact HR corridor, so the watch shows the bpm range Intervals worked out
from its own stored LTHR (172).

The new generator output, multiplied by 172, gives the "expected" column
in the watch notes:

| step | target | × 172 |
|---|---|---|
| Warm-up easy | 68–75 % | 117–129 |
| Tempo | 88–93 % | 151–160 |
| Float | 75–82 % | 129–141 |
| Cool-down | 65–72 % | 112–124 |

The targets are still `%lthr` percentages. Intervals turns them into bpm
when it exports, so the watch's own LTHR no longer changes them. The
earlier `units: "bpm"` and `start_bpm`/`end_bpm` tries stay out.

**Not verified end to end.** I had no API access and pushed nothing, as
the ground rules require. To confirm: run `gen.py`, push the event, check
that `GET /events/{id}` returns `hr.start` and non-empty `workout_doc.steps`,
sync through Garmin Connect, and look for 151–160 on the Tempo step. That
range is not one of the watch's zone edges, so seeing it proves the fix.

## Which parts of the colleague's note applied

- **Applied: the main finding, "use `start`, not `value`".** It matches
  our symptom exactly: the API accepts the event, but the watch shows its
  own zone bands. It also matches our LTHR numbers (Intervals 172, watch
  168) and the expected values (75–82 % → 129–141).
- **Applied: keep `%lthr` percentages and avoid absolute bpm or
  `start_bpm`/`end_bpm`.** Our notes record the same failures (214–249 bpm,
  and a constant 101).
- **Not applied: the top-level `description` in Intervals' text grammar.**
  That trap is about steps not appearing in the Intervals web UI. Nobody
  reported that problem here, and our readback shows `workout_doc.steps`
  populated. The note also warns that if Intervals can't parse a
  description, it wipes both representations. Adding an untested
  description would put a working workout at risk to fix a problem we
  don't have. If steps ever stop showing in the web UI, the note's grammar
  rules apply: `m` means minutes, distances use `mtr`/`km`, no bare `Z<n>`
  outside cycling, and no label may start with a digit.
- **Not applied: the steps for reproducing and pushing a test event.**
  They need credentials and an external API, which is outside this task's
  ground rules.
