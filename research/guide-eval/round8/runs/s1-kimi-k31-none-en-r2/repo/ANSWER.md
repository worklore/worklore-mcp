# Fix

Updated `hr_target` in `gen.py` to add `"range": true` to heart-rate targets. The targets still use `%lthr` and retain the planned `value` and `end` percentages.

Previously, the payload supplied two endpoints without explicitly identifying the target as a range. Garmin therefore reduced the targets to its own heart-rate zone bands. Marking them as ranges requests custom low/high corridors instead of zone targets.

For the tempo plan, the generated corridors remain 68–75%, 88–93%, 75–82%, and 65–72% LTHR, now each with the range marker.

# Verification

Ran `python3 gen.py plans/tempo-run.json` and checked the resulting event programmatically. All four HR targets have the planned bounds and `"range": true`; the repeat count and other workout structure are unchanged. No event was deployed or sent to any external service, so watch behavior has not been re-tested.
