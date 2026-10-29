# Answer: HR targets clamped to the watch's zones

## What changed

`gen.py`, `build_step()`: when a step has `hr_pct`, the output now sets
`"target": "HR"` alongside the `hr` object. Nothing else changed.

Regenerating `plans/tempo-run.json` now produces the same payload as
`readback/event-184233-as-sent.json` plus four `"target": "HR"` lines, one per
HR step (the warm-up, both tempo/float steps inside the repeat, and cool-down).

## Why

The sent payload had an `hr` object with `units: "%lthr"` but no step-level
target type. Intervals.icu's workout model keys each step's target by type
(`HR`, `POWER`, `PACE`), and without it the step has no explicit HR target.
The watch then shows Garmin's zone-band target instead of the planned corridor,
which matches what `readback/watch-notes.md` reports: every planned range
came back as a zone edge (118–137, 151–162, 137–151), and changing LTHR only
moved the bands.

## What I could not verify

- **The fix is not confirmed on the watch.** I did not push anything. Pushing or
  checking the event against the live API would be an external action, and the
  brief was to fix the generator only. The next step is to push a regenerated
  event (`python3 gen.py plans/tempo-run.json > event.json && ./push.sh event.json`),
  re-sync, and check the displayed ranges against 117–129 / 151–160 / 129–141 / 112–124.
- **I could not confirm the `units` enum.** A web search did not turn up the
  official schema for HR `units` or how Intervals exports `%lthr` targets to
  Garmin. If the watch still shows zone bands after the `target` fix, the
  remaining suspect is the export mapping of `%lthr` ranges to Garmin zone
  targets. The earlier `units: "bpm"` attempt produced 214–249 bpm, which
  suggests those values were computed incorrectly. Recomputing bpm from LTHR
  (`round(172 * pct / 100)`) in `gen.py` is the fallback to try, but it needs
  checking against the API output before it is trusted.
- The `start_bpm` / `end_bpm` attempt is not something this generator emits, so
  it is not addressed here.

## Files

- `gen.py`: added `"target": "HR"` for steps with `hr_pct`.
- `ANSWER.md`: this note.

Nothing was committed, pushed, or sent to any external service.
