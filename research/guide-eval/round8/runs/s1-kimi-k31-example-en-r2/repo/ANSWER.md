# HR target fix

Changed `hr_target()` in `gen.py` to emit the lower HR bound as `start` instead of `value`. Targets now have the form:

```json
{"units": "%lthr", "start": 68, "end": 75}
```

`value`/`end` selects Intervals.icu's zone-mapped Lap-HR target path during FIT export, so Garmin replaces the planned corridor with one of the watch's local zone bands. `start`/`end` selects an Instant-HR corridor, preserving the raw bpm range calculated by Intervals. The units remain `%lthr`, so Intervals continues to convert the planned percentages using its stored LTHR.

## Parts of the colleague's note applied

- Applied the `value` → `start` lower-bound rename while retaining `end`.
- Kept HR values as `%lthr` percentages rather than absolute bpm.

The failed `bpm` and `start_bpm`/`end_bpm` variants were not used. The note about the top-level `description` text grammar did not apply to this fix: this generator emits `workout_doc` only, and the reported problem was HR targeting rather than web-UI step rendering.

## Validation

Generated `plans/tempo-run.json` and checked all four HR targets, including both repeated steps. Every target uses `%lthr` with the planned `start`/`end` values and none contains `value`. No event was pushed and no external service was contacted, so watch-side behavior was not re-tested here.
