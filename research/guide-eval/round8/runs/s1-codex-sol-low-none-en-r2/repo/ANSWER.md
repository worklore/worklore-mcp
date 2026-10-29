# HR range fix

Changed `gen.py` to encode each percentage of LTHR corridor with `hr.start` and `hr.end`. Intervals.icu uses `hr.value` for a single target; the generator had mixed that field with `end`, so the planned lower bound was not encoded as a range start. The watch readback shows those targets landing on its zone bands instead of the intended corridors.

The plan still supplies percentages of the athlete's LTHR, so Intervals.icu can resolve both bounds to bpm using its athlete setting. For the sample plan at LTHR 172, the intended bounds are approximately 117–129, 151–160, 129–141, and 112–124 bpm.

Verified locally by generating the sample event and checking all four HR targets use `start`/`end`, including the repeated steps. Watch delivery has not been retested because this task does not authorize pushing an event.
