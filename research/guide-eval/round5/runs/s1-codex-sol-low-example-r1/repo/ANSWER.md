# HR corridor fix

Changed `gen.py` so each HR target uses `{"units": "%lthr", "start": low, "end": high}`. The previous `value` key produced a zone-mapped target: the readback retained the planned percentages, but the watch displayed its own zone boundaries. The `start`/`end` shape selects the instant HR corridor described in the colleague's note, while `%lthr` keeps the conversion based on the LTHR stored in Intervals.

The note's `value` → `start` finding and advice to retain `%lthr` apply here. Its `bpm` and `start_bpm` failures also match the local watch notes, so neither is used. The description grammar advice does not apply to this reported issue: the saved event already has populated `workout_doc.steps`, and there is no reported web UI rendering failure.

Verified locally that the generated tempo run has `start`/`end` HR ranges at every step, including repeats, and no HR `value` keys. A fresh Intervals export and watch sync are still needed to verify the watch display; no external service was contacted.
