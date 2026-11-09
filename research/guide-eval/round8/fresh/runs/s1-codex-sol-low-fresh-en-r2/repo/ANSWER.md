# Generator fix

`gen.py` now emits each HR range as `%lthr` with `start` and `end`, instead of `value` and `end`. The old shape was accepted by the API but exported as a zone target, which explains why the watch displayed its own zone boundaries. Explicit endpoints preserve the planned corridor when Intervals converts it using its LTHR.

The event now also includes a top-level workout `description` in Intervals.icu's text grammar, with repeat blocks. The current export path parses that description for device sync; a populated `workout_doc` alone does not establish that the workout will export as intended.

Verified locally with the tempo-run plan: all four HR ranges match the input, and the description contains the three-repeat block. I did not sync to a watch, so the device result remains unverified.

References: [Intervals.icu API discussion](https://forum.intervals.icu/t/api-access-to-intervals-icu/609), [API workout export discussion](https://forum.intervals.icu/t/events-created-via-api-with-workout-doc-the-web-download-produces-an-empty-fit-while-the-api-download-does-not-which-representation-feeds-device-sync/132326), [HR corridor readback example](https://worklore.dev/s/2026-05-12-exact-hr-corridors-on-garmin-from-intervals-icu-api-workouts).
