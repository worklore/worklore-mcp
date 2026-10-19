# HR targets clamped to watch zones

## Cause
`gen.py` sent a hand-built `workout_doc` (`hr: {units: "%lthr", value, end}`).
In Intervals.icu `workout_doc` is the *parsed output* of the workout text in
`description`; the API echoes it back (so `steps` looked populated), but it is
not the authoritative input. The export to Garmin therefore didn't get a proper
HR range target and the watch fell back to its own zone bands. The earlier
`bpm` / `start_bpm` experiments were the same wrong-field problem.

## Change
`gen.py` now emits the workout in Intervals' workout text syntax in
`description` (e.g. `- Tempo 8m 88-93% LTHR`, repeats as `3x` + steps) and no
longer sends `workout_doc`. Intervals parses this itself and converts to bpm
from its LTHR (172) at export. Plan files and `push.sh` are unchanged.

## Not verified
I could not push (no external calls allowed) or see the watch. Please push
`python3 gen.py plans/tempo-run.json`, check that `workout_doc` read-back has
the 68–75 / 88–93 % ranges, and that the watch shows ~151–160 for Tempo. If the
watch still shows zones, check the Garmin export/sync setting in Intervals
(HR target as range vs. zone) next.
