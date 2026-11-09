# Fix

Changed `hr_target()` in `gen.py` to emit HR targets as `{"units": "%lthr", "start": lo, "end": hi}` instead of using `value` for the lower bound.

`value`/`end` selects Intervals' lap-HR, zone-mapped target path, so Garmin clamps the result to its own HR zones. `start`/`end` selects an instant-HR corridor, preserving the planned range. Keeping `%lthr` lets Intervals convert the percentages using its stored LTHR at FIT-export time.

## Colleague's note

The applicable part was the `value` → `start` key rename for exact HR corridors, together with retaining `%lthr` percentage targets. The alternative `bpm` and `start_bpm`/`end_bpm` encodings were not used. The bonus guidance about the top-level `description` text grammar did not apply to this HR-target fix.
