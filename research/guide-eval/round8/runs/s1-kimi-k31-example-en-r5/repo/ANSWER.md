# Fix

Changed `hr_target` in `gen.py` to emit HR corridors as:

```json
{"units": "%lthr", "start": <low>, "end": <high>}
```

The lower-bound key was previously `value`. In the Intervals.icu FIT export, `value`/`end` selects a zone-mapped Lap-HR target, which lets the watch replace the planned corridor with its own zone edges. `start`/`end` selects an Instant-HR corridor, preserving the bpm range calculated by Intervals.icu. The percentages and `%lthr` units are unchanged, so Intervals still performs the conversion using its stored LTHR.

# Colleague's note

Applied the central `start`/`end` guidance and the recommendation to keep percentage-of-LTHR targets rather than absolute bpm. The earlier failed `bpm` and `start_bpm`/`end_bpm` shapes were background evidence, not changes made here. The top-level `description` grammar advice did not apply: this generator emits `workout_doc` directly, and the readback already contains populated steps.

# Verification

Ran `python3 gen.py plans/tempo-run.json` and validated all four generated HR targets. Their lower bounds are now under `start`, their upper bounds remain under `end`, all use `%lthr`, and none contains `value`. No event was pushed and no watch sync was performed.
