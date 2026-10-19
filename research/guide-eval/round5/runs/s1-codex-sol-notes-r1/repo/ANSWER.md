# HR corridor fix

Changed `gen.py` to emit each HR target as `{"units": "%lthr", "start": low, "end": high}`. The previous `value` field caused Intervals.icu to export a zone-mapped target, so Garmin displayed the watch's zone boundaries instead of the planned range. Using `start` makes it an instant-HR corridor; Intervals computes its bpm endpoints from the athlete's LTHR.

Verified locally that the generated tempo-run event uses `start` and `end` for every HR step, including steps inside the repeat block. A new watch sync was not performed.
