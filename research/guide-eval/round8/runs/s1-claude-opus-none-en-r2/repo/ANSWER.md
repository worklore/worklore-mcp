# HR targets clamped to watch zones — what changed

## Diagnosis

- The watch always shows one of *its own* zone bands, and those bands move when
  the watch's LTHR changes. That means the Garmin workout carries an HR **zone
  number**, not a custom bpm range; the watch resolves the number against its
  own zones. A custom range would be fixed bpm and ignore the watch's LTHR.
- The zone picked each time is the watch zone containing the bpm of our
  *upper* bound (75%→129 Z2, 93%→160 Z4, 82%→141 Z3, 72%→124 Z2), so our
  low/high pair was not being carried through as a range at all.
- The cause is the target object `gen.py` hand-built:
  `{"units": "%lthr", "value": lo, "end": hi}`. In Intervals' `workout_doc`,
  `value` is a single-value target; a range is `start`/`end`. Mixing them gives a
  malformed target that Intervals stored as-is (the readback is a byte-for-byte
  echo with no resolved/computed fields — "accepted" only means it was stored,
  not that it was understood) and exported as a zone rather than a range.
- The earlier tries (`units: "bpm"` → 214–249, `start_bpm`/`end_bpm` → 101)
  failed the same way: guessed field names / units in a hand-written
  `workout_doc` that Intervals doesn't interpret the way we assumed. (The
  readings look like Garmin's FIT HR encoding, where custom bpm values carry a
  +100 offset, getting mangled.)

## Fix (`gen.py`)

The generator no longer hand-builds `workout_doc`. It writes the workout as
Intervals **workout text** in the event `description`, which is the input
Intervals actually parses and validates:

```
- Warm-up easy 10m 68-75% LTHR

3x
- Tempo 8m 88-93% LTHR
- Float 2m 75-82% LTHR

- Cool-down 5m 65-72% LTHR
```

Intervals builds the `workout_doc` from this itself, converts `68-75% LTHR` to bpm
from the athlete's LTHR (172) and exports each step as an explicit low–high HR
range. So the watch should show 117–129, 151–160, 129–141 and 112–124, whatever
LTHR the watch has detected. Targets stay as %LTHR, as the README specifies.
Single-value targets (`[x, x]`) come out as `x% LTHR`; durations that aren't
whole minutes come out in seconds. README updated to match.

## Not verified

Per the ground rules I didn't push anything, so this hasn't been checked on
the watch. To confirm:
1. `python3 gen.py plans/tempo-run.json > event.json && ./push.sh event.json`
2. GET the event: its `workout_doc` steps should now have `hr` with
   `start`/`end` plus resolved bpm values (no longer an exact echo of what we
   sent).
3. Sync to the watch and check that the step targets read 151–160 and so on, not
   the zone edges.

If you'd rather keep sending `workout_doc` directly, the minimal change is
`{"units": "%lthr", "start": lo, "end": hi}` in `hr_target`. But the
description route has Intervals' own parser fill in the doc, which avoids
guessing at the schema again.
