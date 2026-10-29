# HR target fix

Changed `gen.py` to emit each HR corridor as `{"units": "%lthr", "start": low, "end": high}`. The previous `value` lower bound is the shape associated with zone mapped Lap HR targets, which matches the watch readback: all four displayed ranges were watch zone bands. Using `start` selects the Instant HR corridor shape described in the colleague's note, so Intervals can export the planned percentage bounds against its stored LTHR (172 bpm).

The note's `start`/`end` key distinction and `%lthr` units apply here. Its warning against absolute `bpm` and `start_bpm`/`end_bpm` also matches the failed attempts in `readback/watch-notes.md`. The separate top level `description` advice does not address this issue: the API readback already contains populated `workout_doc.steps`, and there is no reported web UI rendering problem. I did not change description generation.

Local verification: generated the sample plan and checked that all four HR targets use `start`/`end`, retain their planned percentages, and contain no `value` key. Watch behavior still needs a sync to verify; no event was pushed from this workspace.
