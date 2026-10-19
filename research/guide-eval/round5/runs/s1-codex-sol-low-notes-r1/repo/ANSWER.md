# HR corridor fix

Changed `gen.py` to emit HR targets as `{"units": "%lthr", "start": low, "end": high}` instead of using `value` for the lower bound. This applies to every step, including steps inside repeats.

The watch readback shows the old `value`/`end` targets displayed as its own HR zone bands. The local end-to-end investigation in `notes/exact-hr-corridors-on-garmin-from-intervals-icu-api-workouts.md` found that `start`/`end` selects an instant HR corridor, so Intervals exports the planned percentage-of-LTHR bounds as bpm. The plan percentages remain unchanged.

Verified locally that the generated tempo run has the expected `start`/`end` targets for all four distinct steps. No event was pushed or watch sync performed.
