# HR corridors snapping to watch zones — fix

## What changed

`gen.py`, `hr_target()`: HR ranges are now sent as

```json
{"units": "%lthr", "start": 68, "end": 75}
```

instead of

```json
{"units": "%lthr", "value": 68, "end": 75}
```

A step whose low and high are equal is sent as a single `{"units": "%lthr", "value": N}`.

Units are still `%lthr`, so Intervals keeps converting to bpm from the athlete's LTHR (172) at export, as the README describes.

## Why

In an Intervals.icu `workout_doc` target, `value` is a **single** target and a **range** uses `start` + `end`. We sent `value` + `end`, which is neither one. Intervals accepted it and stored it unchanged (the readback looks fine), but no range was ever defined.

The readback numbers show what the watch actually received. Every displayed band is the watch zone that contains the step's **upper** bound (%LTHR × 172):

| step | upper bound | watch zone containing it | displayed |
|---|---|---|---|
| Warm-up | 75% → 129 | Z2 118–137 | 118–137 ✓ |
| Tempo | 93% → 160 | Z4 151–162 | 151–162 ✓ |
| Float | 82% → 141 | Z3 137–151 | 137–151 ✓ |
| Cool-down | 72% → 124 | Z2 118–137 | 118–137 ✓ |

Two other readings don't fit the data. The lower bound (`value`) alone would put the warm-up in Z1, since 117 < 118. The midpoint would put the Float in Z2, since it's 135. So the lower bound was dropped, and the leftover single value was exported as a heart-rate zone target rather than a custom bpm range. That also explains why changing the watch's LTHR only moved the bands. With `start`/`end` the step is a real range, and Intervals can export it as a custom HR low/high in bpm.

The earlier workarounds in the notes were wrong turns, and I didn't bring them back:
- `units: "bpm"` gave 214–249.
- `start_bpm`/`end_bpm` aren't fields Intervals recognises, which gave a constant 101, i.e. an empty target in Garmin's offset encoding.

## Not verified

I followed the ground rules: nothing was pushed, and I made no calls to Intervals or Garmin. The fix rests on the `workout_doc` field semantics and on the readback numbers matching exactly as shown above. It hasn't been tested end to end. To confirm:

1. `python3 gen.py plans/tempo-run.json > event.json && ./push.sh event.json`
2. Sync the watch. The Tempo step should show **151–160** and the Float step **129–141**, not zone edges.
