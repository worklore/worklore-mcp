# HR range generator fix

The event in `readback/` contains HR objects such as `{ "units": "%lthr", "value": 88, "end": 93 }`. That is not the documented shape for a range (`start` and `end`), and the API readback only shows that the object was stored. The watch displayed its zone boundaries instead of the requested corridors.

I changed `gen.py` to send an HR-targeted event with a workout-builder `description`, leaving out the hand-built `workout_doc`. Intervals.icu documents this as the event creation path: it parses `88-93% LTHR` as a range and a `3x` block as a repeat. The generator puts blank lines around repeat blocks as required by that syntax, and keeps each step label as cue text. `README.md` now describes the actual payload.

For `plans/tempo-run.json`, the generated description contains `68-75% LTHR`, `88-93% LTHR`, `75-82% LTHR`, and `65-72% LTHR`; it contains no zone targets or absolute bpm targets. At the configured 172 bpm LTHR, those are the intended approximate 117–129, 151–160, 129–141, and 112–124 bpm corridors. The values on Garmin still depend on Intervals.icu resolving the athlete's LTHR and completing Garmin sync.

Verified locally by generating and inspecting the event JSON. No event was posted and no watch sync was run, so the watch display remains to be confirmed on the next authorized push.

References: [Intervals.icu API guidance](https://forum.intervals.icu/t/api-access-to-intervals-icu/609?page=22) and [workout builder syntax](https://forum.intervals.icu/t/workout-builder-syntax-quick-guide/123701).
