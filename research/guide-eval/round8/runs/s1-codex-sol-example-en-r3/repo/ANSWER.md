# HR corridor fix

Changed `gen.py` so each HR target uses `{ "units": "%lthr", "start": low, "end": high }` instead of `value` for the lower bound. The supplied readback shows that the old shape was accepted by Intervals but appeared on the watch as its local zone bands. The colleague's finding that `start`/`end` selects an Instant HR corridor applies here; keeping `%lthr` lets Intervals calculate bpm from its stored LTHR.

The colleague's `bpm` and `start_bpm`/`end_bpm` failures also match the earlier attempts recorded in `readback/watch-notes.md`, so neither is used. The top-level description and Intervals text grammar advice does not address the reported watch corridor problem; the readback already has populated `workout_doc.steps`, and there is no reported web UI rendering failure. No external event was posted or watch sync performed, so the watch result still needs an end-to-end check.

Local check: generating `plans/tempo-run.json` produces the four planned HR ranges with `start`/`end` and no `value` keys, including both steps inside the repeat block.
