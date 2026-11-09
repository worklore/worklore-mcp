# HR target fix

Changed `hr_target` in `gen.py` to emit `{"units": "%lthr", "start": lo, "end": hi}` instead of using `value` for the lower bound.

`value`/`end` selects Intervals' zone-mapped Lap-HR target, which lets the watch replace the planned corridor with its own HR zone band. `start`/`end` selects an Instant-HR corridor, preserving the percentages of LTHR so Intervals can convert them to the intended bpm range during FIT export.

## Colleague's note

Applied the confirmed `start`/`end` HR target shape and retained `%lthr` percentages rather than absolute bpm. The failed `bpm` and `start_bpm`/`end_bpm` alternatives were not used.

The top-level `description` grammar and web-UI parsing advice did not apply: this generator creates structured `workout_doc.steps` directly, does not emit a top-level description, and the readback confirms those steps were populated and accepted. No description was added.

## Verification

Ran the generator against `plans/tempo-run.json` and checked all four HR targets. Their corridors remain 68–75, 88–93, 75–82, and 65–72 `%lthr`; every target now has exactly `units`, `start`, and `end`, with no `value` key. No external request or watch sync was performed, so watch rendering was not reverified here.
