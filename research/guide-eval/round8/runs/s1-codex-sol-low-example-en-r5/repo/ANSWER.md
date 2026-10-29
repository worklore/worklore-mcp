# HR corridor fix

Changed `gen.py` to emit each HR target as `{"units": "%lthr", "start": low, "end": high}`. The previous `value`/`end` shape is present in the accepted API readback, while `watch-notes.md` records that the watch displayed its own zone bands instead of the planned bounds. The colleague's `start`/`end` finding directly applies to this symptom and preserves the plan's LTHR percentages for Intervals to convert.

The note's warnings about absolute `bpm` targets and `start_bpm`/`end_bpm` also apply: the watch notes document failed trials of both, so this fix uses neither. Its top-level `description` advice does not apply to the reported issue: the readback has populated `workout_doc.steps`, and there is no report of missing steps in the Intervals UI. I did not add a description or change the plan grammar.

Verified locally that the generated event contains `start`/`end` on every HR step, including repeated steps, with the planned percentages and no `value` key. A watch sync was not performed, so the corrected watch display remains to be confirmed on the device.
