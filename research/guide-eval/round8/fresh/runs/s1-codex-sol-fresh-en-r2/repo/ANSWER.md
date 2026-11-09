# HR range export fix

`gen.py` now writes each percentage-of-LTHR corridor as `hr: {"units": "%lthr", "start": low, "end": high}`. Previously it wrote `value` for the low endpoint and `end` for the high endpoint. In Intervals.icu's workout document format, a single target uses `value`; a range uses `start` and `end`. The old hybrid was accepted and read back by the event API, but did not express the planned range correctly to the workout exporter. This explains why the watch showed its zone boundaries rather than the requested endpoints.

For the supplied plan, the intended exported limits remain 68–75%, 88–93%, 75–82%, and 65–72% of the Intervals.icu LTHR of 172 bpm (approximately 117–129, 151–160, 129–141, and 112–124 bpm). The generator keeps percentage targets so Intervals.icu can resolve them using the athlete's sport settings. Changing the watch's LTHR cannot repair the malformed range, and the prior `bpm` and `start_bpm`/`end_bpm` attempts used the wrong representation.

`python3 -m unittest test_gen.py` verifies the range fields in ordinary and repeated steps. No event was sent, and the Garmin display still needs a real device readback after the corrected workout is synced.

Reference: [Intervals.icu workout builder example showing `%lthr` ranges with `start` and `end`](https://forum.intervals.icu/t/workout-builder/1163/1123).
