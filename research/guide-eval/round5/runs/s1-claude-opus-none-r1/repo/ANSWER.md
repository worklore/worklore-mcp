# HR corridors clamped to watch zones: fix

## Cause
`gen.py` wrote each HR corridor as

```json
"hr": {"units": "%lthr", "value": 68, "end": 75}
```

In an Intervals.icu `workout_doc` step, a range is written as `start` + `end`.
`value` means a single target. Intervals took the step as a single %LTHR
target and ignored `end`. When it exports a single HR target to Garmin, it
sends a **zone number** instead of a bpm range. The watch then shows its own
band for that zone. This matches every symptom in `readback/watch-notes.md`:

- Each step shows exactly one of the watch's zone bands (Warm-up → Z2,
  Tempo → Z4, Float → Z3, Cool-down → Z2).
- Changing the watch's LTHR moves the bands, but the targets stay on zone
  edges. The watch is resolving a zone number against its own zones.
- The API returned the doc unchanged, so nothing was rejected. The field was
  just read differently from what we meant.

The two earlier workarounds were wrong for separate reasons. `"bpm"` is not
an HR unit, and values like 125–145 read as %LTHR give 214–249. And
`start_bpm`/`end_bpm` are fields Intervals computes, not inputs.

## Change (`gen.py`, `hr_target`)
- Corridors are now written as `{"units": "%lthr", "start": lo, "end": hi}`.
  Intervals keeps them as %LTHR, converts them to bpm with the athlete's LTHR
  (172) at export, and sends them as a custom HR range.
- If a plan gives the same low and high value, the generator writes a single
  `value` target, which is the correct form for that case.

Plans and `push.sh` are unchanged. The README is still accurate (HR targets
are %LTHR and Intervals converts them).

## Not done / to verify
I did not push anything (no external calls). To confirm, regenerate and push
(`python3 gen.py plans/tempo-run.json > event.json && ./push.sh event.json`),
then sync. The watch should show roughly 117–129, 151–160, 129–141 and
112–124 bpm. You may want to delete event 184233 first so the old version
doesn't stay on the calendar.
