# HR corridor fix

Changed `gen.py` so each HR target uses `{ "units": "%lthr", "start": low, "end": high }`. The previous `value` lower bound appears to select a zone-mapped target in the Garmin export: the saved event used `value`, and every observed watch range matched a watch zone rather than the planned corridor. `start` is the colleague's applicable finding for selecting an Instant HR corridor while keeping the plan's LTHR percentages.

The note's failed `bpm` and `start_bpm`/`end_bpm` attempts also apply: the watch notes record the same invalid results, so the generator retains `%lthr`. The top-level `description` and text-parser advice does not apply to this reported issue. The API readback already contains populated `workout_doc.steps`, and the record does not show an Intervals web UI rendering problem.

Verified locally that the generated event gives every HR step `start` and `end` with its planned percentages and contains no HR `value`. A new push and Garmin sync were not performed, so watch display of the corrected event remains unverified.
