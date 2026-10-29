# HR corridor fix

Changed `gen.py` so each HR target emits `{"units": "%lthr", "start": low, "end": high}` instead of `value`/`end`. This applies to ordinary steps and steps inside repeats through the shared `hr_target` function.

The API readback shows the old `value`/`end` shape was accepted, while the watch displayed its own zone boundaries rather than the planned corridors. The colleague's finding that `start`/`end` selects an instant HR corridor directly applies here. The plan already uses percentages of Intervals' LTHR, so that part needed no change. With the stored LTHR of 172, the intended corridors remain 117–129, 151–160, 129–141, and 112–124 bpm for warm-up, tempo, float, and cool-down respectively.

The note's `bpm` and `start_bpm`/`end_bpm` failures match the earlier attempts in `readback/watch-notes.md`; neither is used in the fix. Its top-level `description` and text-grammar advice does not address the reported HR clamping: the readback already has populated `workout_doc.steps`, and there is no reported web UI parsing issue.

Verified locally by generating `plans/tempo-run.json`: all four HR targets, including the two inside the repeat, have `%lthr` with `start`/`end` and no `value`. No event was posted or watch sync performed, so watch behavior after this change remains unverified.
