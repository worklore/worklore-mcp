# Fix: HR corridors clamped to the watch's zones

## Cause

`gen.py` wrote every HR target as `{"units": "%lthr", "value": lo, "end": hi}`.
Intervals.icu exports a `value`/`end` target as a lap-HR, zone-mapped target.
The watch then clamps it to its own auto-detected zones (LTHR 168 on this
watch), so 151–160 showed up as 151–162, and 129–141 as 137–151.

`readback/watch-notes.md` has the observations. The earlier `bpm` and
`start_bpm`/`end_bpm` attempts were also wrong (see the notes in
`notes/exact-hr-corridors-on-garmin-from-intervals-icu-api-workouts.md`).

## Change

`gen.py`, `hr_target()`: the lower bound is now keyed as `start` instead of
`value`:

```python
return {"units": "%lthr", "start": lo, "end": hi}
```

The docstring explains why the key matters, so nobody reverts it to `value`.

Per the notes file, `{start, end}` exports as an instant-HR corridor. The
watch then shows the bpm Intervals computes from the athlete's LTHR (172),
independent of the watch's own zones. Units stay `%lthr`, so the targets still
follow the LTHR stored in Intervals.

## Verification

- `python3 gen.py plans/tempo-run.json` now emits `start`/`end` for all four
  HR steps: 68–75, 88–93, 75–82, 65–72 (% LTHR). The durations, labels, and
  repeat structure are unchanged.
- Expected on the watch (× 172): 117–129, 151–160, 129–141, 112–124 bpm.

## Not verified here

- I have not pushed this event or checked it on a watch. Both need the
  Intervals API key and the device, and I was asked not to submit anything
  externally.
- The `start`/`end` behavior comes from the notes file, which says it was
  verified end-to-end. I did not re-test it. If the watch still shows zone
  edges after a push and Garmin sync, check the readback with
  `GET /events/{id}` first.

## Not changed

- The top-level `description` (Intervals' text grammar, used for the web UI
  step chart) is still not generated. The notes describe it, but it is outside
  the HR-range problem, so I left it alone.
