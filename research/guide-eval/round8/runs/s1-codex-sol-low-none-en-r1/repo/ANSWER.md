# HR range fix

Changed `gen.py` to emit each heart rate corridor as `hr: {"units": "%lthr", "start": low, "end": high}`. Intervals.icu represents a range with `start` and `end`; `value` represents a single target. The generator had mixed `value` with `end`, so the intended lower bound was not encoded as a range and the watch displayed its own zone band.

The plan remains in percent of LTHR, so Intervals.icu can resolve it against the athlete's threshold. The earlier absolute BPM and `start_bpm`/`end_bpm` attempts do not use this range representation.

Verified locally that all four generated targets, including steps inside the repeat block, contain `start`/`end` and no `value`. A watch sync was not performed.
