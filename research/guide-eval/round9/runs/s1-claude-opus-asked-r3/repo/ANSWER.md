# HR corridors clamped to watch zones — fix

## What changed
`gen.py`, `hr_target()`: the HR target's lower bound key changed from `value` to `start`.

```diff
- return {"units": "%lthr", "value": lo, "end": hi}
+ return {"units": "%lthr", "start": lo, "end": hi}
```

Units are still `%lthr`, so Intervals still converts using its own LTHR (172) at export.

## Why
Intervals.icu's FIT export chooses the target type from the key names:

- `{value, end}` is exported as a **zone-mapped (Lap-HR) target**. The Garmin
  snaps it to the watch's own HR zones. That matches `readback/watch-notes.md`:
  every step showed up as a full watch zone (118–137, 151–162, …), and changing
  the watch's LTHR moved the bands without fixing them.
- `{start, end}` is exported as an **Instant-HR corridor**. The watch shows the
  bpm that Intervals worked out (e.g. Tempo 88–93% × 172 → 151–160, Float →
  129–141), whatever LTHR the watch has detected.

The earlier tries fail for known reasons. `units: "bpm"` gets read as a
percentage, which gave 214–249. `start_bpm`/`end_bpm` isn't in the schema, so it
was silently dropped and the watch fell back to 101. The API takes
`{value, end}` without complaint, so the readback looked fine even though the
export mode was wrong.

Source: worklore story `2026-05-12-exact-hr-corridors-on-garmin-from-intervals-icu-api-workouts`.
It describes the same symptom, and the cause was confirmed from a workout
built in the Intervals UI with the "Instant HR" toggle and then read back
through the API.

## Not done / to verify
- Nothing was pushed (no external calls, as instructed). To confirm, regenerate
  and push, sync the watch, and check that Tempo shows 151–160 and Float 129–141.
- `readback/event-184233-as-sent.json` still shows the old payload, since it's
  a record of what was sent.
- The same story says the Intervals **web UI** only renders steps from a
  top-level `description` written in Intervals' text grammar. That isn't part
  of this bug, so I didn't add it.
- Unrelated: `README.md` has what looks like a real `INTERVALS_API_KEY` in
  plain text, and `config/intervals.toml` is tracked. You may want to rotate
  the key and remove both from the repo.
