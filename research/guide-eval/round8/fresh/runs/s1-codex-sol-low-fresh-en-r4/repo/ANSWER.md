# HR corridor fix

`gen.py` now emits each HR range as `%lthr` with `start` and `end`. The previous `value`/`end` shape selected the zone or lap HR path, which explains why the Forerunner showed its own zone boundaries. Percentages stay relative to the LTHR stored in Intervals.icu; the generator does not bake in the watch's threshold or use absolute `bpm` fields.

The event also includes an Intervals workout `description` with the same ranges, repeat block, and `hr=1s` on every HR step. This makes the text representation available to the current workout export path and requests Instant HR for Garmin. `workout_doc.target` explicitly selects HR.

I generated the sample event locally and checked that all four corridors and the three-repeat block appear in both representations. No event was sent to Intervals.icu, so watch display still needs an end-to-end check on a newly exported workout.

References: [Intervals.icu API workout fields](https://forum.intervals.icu/t/downloading-planned-workouts-from-the-api/93737), [Instant HR option](https://forum.intervals.icu/t/power-and-hr-targets-for-garmin-workouts/2926), [description and export behavior](https://forum.intervals.icu/t/events-created-via-api-with-workout-doc-the-web-download-produces-an-empty-fit-while-the-api-download-does-not-which-representation-feeds-device-sync/132326).
