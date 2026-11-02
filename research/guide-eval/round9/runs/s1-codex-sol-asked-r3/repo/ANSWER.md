# HR corridor fix

Changed `gen.py` to emit each planned HR range as `hr: {"units": "%lthr", "start": low, "end": high}`. The generator previously emitted `value` plus `end`; in Intervals.icu's workout format, `value` is a single target and a range uses `start` and `end`. The API preserved the malformed object, but the watch displayed its zone bands instead of the planned corridors. The [Intervals.icu workout builder examples](https://forum.intervals.icu/t/workout-builder/1163?page=55) show this `start`/`end` shape for `%lthr` ranges.

Verified the generated event locally: warm-up 68–75%, tempo 88–93%, float 75–82%, and cool-down 65–72% all have `start`/`end` with no `value`; the three-repeat block remains intact. No event was pushed, so watch behavior still needs a readback after the corrected event is synced.
