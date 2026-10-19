# HR corridors clamped to the watch's zones — fix

## Cause

`gen.py` built every HR target as `{"units": "%lthr", "value": lo, "end": hi}`.
`readback/event-184233-as-sent.json` shows that exact shape, and the API
returned it unchanged. Per the colleague's note, Intervals exports a `value`-keyed
target as a lap/zone-mapped target, so the watch clamps it to its own LTHR zone
bands. That matches `readback/watch-notes.md`: every corridor landed on a zone
edge (118–137, 137–151, 151–162) and never on the planned bpm.

## Change

`gen.py`, `hr_target()`: the lower bound key is now `start` instead of `value`:

```python
return {"units": "%lthr", "start": lo, "end": hi}
```

A comment above it records the reason. Nothing else changed. The units stay
`%lthr`, so the percentages are still converted by Intervals using the LTHR it
stores (172), not the watch's LTHR.

## Verification

- Regenerated `plans/tempo-run.json` locally. All four HR targets now carry
  `start`/`end` and no `value`:
  - Warm-up easy `{units: %lthr, start: 68, end: 75}`
  - Tempo `{units: %lthr, start: 88, end: 93}`
  - Float `{units: %lthr, start: 75, end: 82}`
  - Cool-down `{units: %lthr, start: 65, end: 72}`
- Not verified: I could not push to Intervals or sync the watch here, and the
  ground rules say not to submit anything to external services. Whether the
  watch now shows 129–141 etc. is still unconfirmed. The next step is to run
  `./push.sh event.json`, read the event back, and check the watch face.

## Colleague's note: what applied and what didn't

**Applied**
- Use `start`/`end`, never `value`, for HR targets. This is the one-word fix
  in `gen.py`.
- Keep percentages with `units: "%lthr"`. Intervals converts them at export
  from its own stored LTHR, so the watch's LTHR does not matter.

**Not applied**
- Setting a top-level `description` in Intervals' text grammar. Our event sends
  no `description`. The readback already shows populated `workout_doc.steps`,
  so the parser is not the problem here, and the watch-notes complaint is about
  HR targets, not missing steps. Changing this would be a separate task.
- The `start_bpm`/`end_bpm` and absolute-bpm experiments. We never used those in
  `gen.py`, so there was nothing to revert.

**Not verified**
- The note's claim that `start` produces an Instant-HR corridor on the watch.
  The Intervals and Garmin behavior is only evidence from another athlete's
  case. We confirm it only after a real push and sync.
