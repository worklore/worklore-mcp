# HR target export fix

Changed `gen.py` to emit each planned HR corridor as `hr: {"start": low, "end": high, "units": "%lthr"}` and to set `workout_doc.target` to `"HR"`.

The old generator put the lower bound in `value`, which represents a single target, rather than a range endpoint. It also left the workout's target mode unspecified. In the current Intervals.icu workout format, `start`/`end` represent a range and `target: "HR"` selects heart rate for export. The API readback only showed that the document was stored; it did not prove that Garmin received the intended target. These changes preserve LTHR percentages so Intervals can resolve them using the athlete's threshold, while making the intended corridor explicit.

Verified locally by generating the sample event and checking its four HR targets and workout target. A new watch sync is still needed to confirm the displayed bpm ranges end to end; no external service was contacted with this workout.
