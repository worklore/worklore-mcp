# HR target fix

Changed `hr_target()` in `gen.py` to emit the lower HR bound as `start` instead of `value`:

```json
{"units": "%lthr", "start": 68, "end": 75}
```

`value`/`end` makes Intervals export a Lap-HR, zone-mapped target, so the watch substitutes bands from its own HR zones. `start`/`end` makes it an Instant-HR corridor, preserving the planned range when Intervals converts the percentages to bpm using its stored LTHR. The `%lthr` units and all planned percentages are unchanged.

## Colleague's note

Applied:

- Use `start` and `end`, never `value`, for exact HR corridors.
- Keep targets as percentages of LTHR (`%lthr`), not absolute bpm; Intervals performs the bpm conversion at FIT-export time.

Not applicable:

- The failed `bpm` and `start_bpm`/`end_bpm` alternatives were supporting evidence, not part of the fix.
- The top-level `description` and Intervals text-grammar guidance concerns web-UI step rendering. This generator does not create that field, and the reported problem is HR target mapping; the existing readback already has populated `workout_doc.steps`.

## Verification

Ran the generator against `plans/tempo-run.json` and checked all four HR targets, including those inside the repeat block. They retain the planned corridors `(68, 75)`, `(88, 93)`, `(75, 82)`, and `(65, 72)`, use `%lthr` with `start`/`end`, and contain no `value` key. No event was pushed and no watch sync was performed.
