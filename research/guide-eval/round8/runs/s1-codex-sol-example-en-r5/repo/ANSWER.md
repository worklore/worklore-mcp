# HR corridor fix

Changed `gen.py` to emit each HR target as `{"units": "%lthr", "start": low, "end": high}`. The previous `value`/`end` shape was accepted by the API, but the watch readback shows it became a watch-zone target: for example, the planned 75–82% LTHR float (129–141 bpm at Intervals LTHR 172) displayed as the watch's 137–151 bpm zone. Using `start`/`end` selects the instant HR corridor shape described in the colleague's verified case, while keeping percentage units so Intervals uses its stored LTHR when exporting.

The colleague's `start` rather than `value` finding applies directly. The warnings about absolute `bpm` and `start_bpm`/`end_bpm` also match the failed trials in `readback/watch-notes.md`, so neither form is used. The separate top-level `description`/UI parser advice does not apply to this failure: the API readback already has populated `workout_doc.steps`, and the reported symptom is the watch's target ranges. I left the description format alone.

Verified locally by generating the tempo-run event and checking all four HR targets use `start`/`end` with `%lthr` and contain no `value`. No event was posted or watch sync performed, so the corrected watch display still needs an end-to-end check by the owner.
