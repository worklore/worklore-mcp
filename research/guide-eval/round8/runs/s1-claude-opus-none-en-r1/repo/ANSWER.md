# HR ranges snapping to watch zones — fix

## What changed

`gen.py`, `hr_target()`: HR corridors are now emitted as

```json
"hr": {"units": "%lthr", "start": 68, "end": 75}
```

instead of

```json
"hr": {"units": "%lthr", "value": 68, "end": 75}
```

If a plan step has the same low and high (`hr_pct: [x, x]`), it still emits a
single `{"units": "%lthr", "value": x}`.

## Why

In Intervals' `workout_doc`, a target range is written as `start`/`end`.
`value` means a single **fixed** target. `value` + `end` is not a valid range,
so Intervals stored it (which is why the readback looks the same as what we
sent) but treated each step as one fixed HR number. When it exports a fixed HR
target to Garmin, it widens the number to a band. That band comes from the
zone/range settings, not from our plan. So the watch showed whole zone bands
(118–137, 151–162, …), and the bands moved when the watch's LTHR changed.

The readback table supports this: in every step, the band the watch showed is
the watch zone that contains our planned **upper** bound (75 % → 129 → Z2,
93 % → 160 → Z4, 82 % → 141 → Z3, 72 % → 124 → Z2). Our planned span never
reached the watch.

Things I deliberately did not do:
- Absolute bpm (`units: "bpm"`): Garmin's FIT format stores custom HR targets
  as bpm + 100, and earlier tries came out offset (214–249). Keeping `%lthr`
  lets Intervals convert with LTHR 172 at export, as the README intends.
- `start_bpm`/`end_bpm`: these aren't workout_doc fields. They were ignored,
  which is where the constant 101 came from.

## Not verified

Per the ground rules, I didn't push anything to Intervals.icu, so I haven't
confirmed this on the watch. The field names come from Intervals'
`workout_doc` conventions (the same `start`/`end` shape it uses for power and
pace ranges). They are not from an official schema I could check offline. To
confirm:

```
python3 gen.py plans/tempo-run.json > event.json
./push.sh event.json
```

On the watch, Tempo should then read about 151–160 and Float about 129–141.
If it still shows zone edges, check the athlete's Intervals Garmin/HR export
settings to see whether HR targets are being exported as zones.
