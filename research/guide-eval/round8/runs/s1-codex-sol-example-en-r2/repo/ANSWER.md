# HR corridor fix

Changed `gen.py` to emit `{"units":"%lthr","start":low,"end":high}` for every planned HR corridor, including steps inside repeats. The previous `value` lower bound matched the zone-mapped target shape described in the colleague's note and the readback; the watch displayed its own zone edges instead of the planned bounds. `start` selects the instant HR corridor shape while preserving Intervals' LTHR-based percentage conversion.

The applicable parts of the note were the `start`/`end` key shape and keeping `%lthr` rather than switching to absolute `bpm` or `start_bpm`/`end_bpm` (both already failed in the watch notes). The top-level `description` and text grammar advice concern whether steps appear in the Intervals web UI. The existing API readback has populated `workout_doc.steps`, and this task reports a watch target issue, so I did not change description generation.

Local check: generated the tempo-run event and confirmed all four HR targets, including both repeated steps, use `%lthr` with the planned `start`/`end` bounds and contain no `value` key. No event was posted or watch synced, so the Garmin display remains to be verified on the next normal sync.
