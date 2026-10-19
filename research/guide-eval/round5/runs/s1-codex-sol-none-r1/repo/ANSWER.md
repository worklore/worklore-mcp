# HR range fix

Changed `gen.py` to encode each planned HR corridor as `hr: {"units": "%lthr", "start": low, "end": high}`. The previous payload used `value` for the lower bound; in Intervals.icu's workout format, `value` denotes a single target, while `start` and `end` denote a range. This mismatch is the likely cause of the watch showing zone bands instead of the planned corridors.

The plan still specifies percentages of LTHR, so Intervals can resolve them using the athlete's threshold. The generated event was checked against all four planned ranges and the three-repeat block. I did not push a new event, so the watch display has not been verified. The existing event and readback remain a record of the old payload.

Schema reference: [Intervals.icu workout builder example showing an `%lthr` HR range with `start` and `end`](https://forum.intervals.icu/t/workout-builder/1163/1123).
