# HR range fix

Changed `gen.py` to emit each HR corridor as `{ "units": "%lthr", "start": lower, "end": upper }`, including steps inside repeats. The previous `value` key represents a single HR target; it caused the Garmin export to use zone-based targets, matching the bands recorded in `readback/watch-notes.md`. Intervals' range form uses `start` and `end`, so the watch can receive the planned corridor.

The percentages remain relative to the LTHR stored in Intervals (172 bpm for this athlete). That gives expected ranges of 117–129 bpm for warm-up, 151–160 for tempo, 129–141 for float, and 112–124 for cool-down. The watch's own LTHR and zone boundaries should not set those endpoints.

Verified locally by generating the sample event and checking the HR objects in both ordinary and repeated steps. No event was pushed or watch sync performed, so the on-watch result still needs confirmation at the next authorized sync.
