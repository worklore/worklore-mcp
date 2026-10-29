# HR corridor fix

Changed `gen.py` to write each planned HR range as `hr: {"start": low, "end": high, "units": "%lthr"}`. The generator previously wrote `value` for the lower bound. In the Intervals.icu workout format, `value` denotes a single target; a range uses `start` and `end`. That left the lower bound of our corridor unspecified and led to the zone-band targets observed in `readback/watch-notes.md`.

The plan still uses percentages of the athlete's LTHR, so Intervals.icu can resolve the bounds using the athlete's threshold. This change only fixes the range shape; confirming the exact display on the watch requires syncing a newly generated workout.
