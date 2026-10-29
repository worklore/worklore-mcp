# HR target fix

`gen.py` now puts each planned HR corridor in the event's `description` using
Intervals.icu workout-builder syntax, such as `- Tempo 8m 88-93% LTHR`. It
also writes repeat groups as `3x` blocks with the required blank lines around
them. The event name, sport, and date still come from the plan.

The old generator sent `workout_doc` directly, with each range encoded as
`value` plus `end`. Intervals.icu's documented range fields are `start` and
`end`, and its API guidance says uploads should use the workout description
or a workout file so the service compiles the workout. A GET returning the
same `workout_doc` only showed that the JSON was stored; it did not prove the
Garmin export understood those targets. Generating the supported description
lets Intervals parse the percentage ranges and repeat structure itself.

This was checked locally by generating `plans/tempo-run.json` and verifying
all four planned `% LTHR` ranges, the `3x` block, and the absence of a
hand-built `workout_doc`. No event was uploaded, so watch behavior remains to
be confirmed on the next normal sync.

References: [Intervals.icu API upload guidance](https://forum.intervals.icu/t/api-access-to-intervals-icu/609?page=22),
[workout-builder syntax](https://forum.intervals.icu/t/workout-builder-syntax-quick-guide/123701).
