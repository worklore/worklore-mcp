# Fix: HR corridors clamped to the watch's own zones

## Symptom

Every HR corridor from our plans showed up on the watch as one of the
watch's own zone bands (auto-detected LTHR 168: Z2 118–137, Z4 151–162,
Z3 137–151), never the planned range (e.g. 151–160 for the tempo step).
See `readback/watch-notes.md`.

## Root cause

`gen.py` emitted HR targets as `{"units": "%lthr", "value": lo, "end": hi}`.
In Intervals.icu's `workout_doc`, the key name for the lower bound selects
the FIT-export mode:

- `{value, end}` → exported as a **lap-HR / zone-mapped** target, so the
  watch clamps the corridor to its own local zone edges.
- `{start, end}` → exported as an **instant-HR corridor**, and the watch
  displays the raw bpm Intervals computed from *its* stored LTHR (172),
  independent of the watch's auto-detected LTHR.

This also explains the two earlier failed attempts in the watch notes:

- `{units: "bpm", value, end}` — the FIT export misread absolute bpm as a
  percentage, producing the impossible 214–249 bpm display.
- `{start_bpm, end_bpm}` — not part of the schema, so the target was
  silently dropped and the watch fell back to a constant 101.

Reference: [Exact HR corridors on Garmin from Intervals.icu API workouts —
start/end, not value/end](https://worklore.dev/s/2026-05-12-exact-hr-corridors-on-garmin-from-intervals-icu-api-workouts)
(same three symptoms, same fix verified end-to-end).

## Change

`gen.py:13` — renamed the lower-bound key, one word:

```diff
-    return {"units": "%lthr", "value": lo, "end": hi}
+    return {"units": "%lthr", "start": lo, "end": hi}
```

## Verification

- Ran `python3 gen.py plans/tempo-run.json`; every `hr` target now reads
  `{"units": "%lthr", "start": <lo>, "end": <hi>}` (e.g. tempo step
  88–93, which is 151–160 bpm at Intervals' LTHR 172).
- Per the ground rules, nothing was pushed. `readback/event-184233-as-sent.json`
  still shows the old `value`/`end` payload from the last push; it will be
  superseded the next time `./push.sh` runs. After pushing, sync the watch
  and confirm the tempo step displays 151–160, not 151–162.

## Related (not changed)

The same source notes a separate trap: the Intervals web UI renders steps
from a top-level `description` in Intervals' text grammar, so API-only
`workout_doc` events can be invisible in the UI. That affects UI display,
not the watch, so it's out of scope here — worth a follow-up if you want
the steps visible in the Intervals UI too.
