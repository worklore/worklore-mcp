# HR corridors clamped to the watch's zones — fix

## What changed

`gen.py`, `hr_target()`: the corridor's lower bound is now sent as `start`
instead of `value`.

```diff
-    return {"units": "%lthr", "value": lo, "end": hi}
+    return {"units": "%lthr", "start": lo, "end": hi}
```

The output still uses `%lthr` percentages, so Intervals converts them to bpm
with its own stored LTHR (172). No other fields changed.

## Why

The key name decides how Intervals.icu exports the target to the FIT file:

- `{value, end}` is exported as a **zone-mapped (Lap-HR) target**. The Garmin
  snaps it to the watch's own HR zones. That matches `readback/watch-notes.md`:
  every step showed as one of the watch's zone bands (118–137, 151–162, …), and
  changing the watch LTHR moved the bands but they stayed zone edges.
- `{start, end}` is exported as an **Instant-HR corridor**. The watch shows the
  bpm Intervals worked out, e.g. 75–82 % × 172 → 129–141. That's the planned
  range, and the watch's own LTHR (168) no longer affects it.

The API accepts both shapes and gives no error. That's why the readback looked
fine (`workout_doc.steps` was populated) even though the watch got the wrong
kind of target. The earlier attempts fail for other reasons: `units: "bpm"` gets
read as a percentage (214–249), and `start_bpm`/`end_bpm` gets dropped, which
leaves Garmin's fallback of 101.

Source: worklore story `2026-05-12-exact-hr-corridors-on-garmin-from-intervals-icu-api-workouts`.
The author found this by building an "Instant HR" step in the Intervals UI and
reading it back through the API. Their result was the same as ours should be:
Intervals LTHR 172, watch LTHR 168, and 75–82 % showing as 129–141.

## Verification done / still needed

- Done locally: `python3 gen.py plans/tempo-run.json` now emits
  `start`/`end` for every HR step, and no `value` keys remain.
- Not done (ground rules: nothing pushed): push the event, read it back with
  `GET /events/{id}`, then sync the watch. Expected on the watch: Warm-up
  117–129, Tempo 151–160, Float 129–141, Cool-down 112–124.

## Notes, not changed

- The same story says the Intervals web UI shows no step chart unless the event
  also has a top-level `description` written in Intervals' text grammar. In that
  grammar `m` means minutes, and a step label must not start with a digit. I
  left this out because it isn't related to the watch problem.
- `README.md` contains what looks like a real Intervals API key
  (`INTERVALS_API_KEY=r9s1…`), and `config/intervals.toml` holds credentials.
  Think about rotating that key and taking it out of the README.
- I did not call worklore's `report_reproduction`, because the ground rules say
  not to report anything to external services.
