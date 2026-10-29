# HR range generator fix

Changed `gen.py` to emit each HR corridor as `{"units":"%lthr","start":low,"end":high}`. The previous `value`/`end` object did not encode a range in Intervals.icu's workout format: `value` is for a single target, while ranges use `start` and `end`. That explains why the accepted event could still reach the watch as a zone band.

The plan percentages and repeat structure are unchanged. A local check of the generated tempo run confirmed all four planned corridors, including both repeated steps. Garmin export and watch display have not been rechecked because that would require an external push.

Format reference: [Intervals.icu workout builder discussion](https://forum.intervals.icu/t/custom-zones-work-started/112132?page=4) (documents the `value`, `start`, and `end` fields on HR targets).
