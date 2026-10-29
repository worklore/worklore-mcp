# HR range fix

`gen.py` now writes each planned HR corridor as `hr: {"units": "%lthr", "start": low, "end": high}` and sets `workout_doc.target` to `"HR"`.

The previous generator put the lower bound in `value`. In Intervals.icu's workout format, `value` denotes a single target; a range uses `start` and `end`. That made the planned corridor a point target, which explains why the watch displayed its own zone band around it. Explicitly selecting HR also makes the intended workout target unambiguous.

I checked the generated tempo run locally: all four distinct steps retain their planned percentage bounds, and the tempo/float pair still repeats three times. I did not push a workout or verify the display on a watch, so the device result remains to be checked after the next authorized sync.
