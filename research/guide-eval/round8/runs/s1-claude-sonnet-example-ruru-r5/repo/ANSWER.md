# Fix: HR corridors clipped to the watch's zones

## Change
`gen.py`, `hr_target()`: `{"units": "%lthr", "value": lo, "end": hi}` -> `{"units": "%lthr", "start": lo, "end": hi}`.

## Why
Per `readback/watch-notes.md`, the API accepts the event and reads it back as sent, but each corridor appears on the watch as one of its own zone bands (e.g. 129–141 planned -> 137–151 shown), and changing the watch LTHR only moves the bands. That matches the colleague's case: in the Intervals FIT export, a lower bound named `value` becomes a Lap-HR/zone target, which the watch clips to its local zones. A lower bound named `start` becomes an Instant-HR corridor in raw bpm computed by Intervals (% x Intervals LTHR 172). Percent units are kept so Intervals converts with its own stored threshold.

Expected on the watch after the fix: 117–129, 151–160, 129–141, 112–124.

## Not verified
I couldn't run the push -> Garmin sync -> watch loop here. Please push a test event, check the watch, and delete the event afterwards.

## What from the colleague's note was useful
- Used: the `value` -> `start` rename (the actual fix), keeping `%lthr` units, and the readback check (non-empty `workout_doc.steps`).
- Already consistent with the note: the earlier `bpm` (214–249) and `start_bpm`/`end_bpm` (constant 101) attempts in watch-notes.md are the failures it describes; neither was reused.
- Skipped: the top-level `description` text grammar (`m` = minutes, `mtr`/`km`, etc.). Our problem isn't the web UI display, and adding a description risks the parser wiping the steps. Worth revisiting if the UI shows no step graph. Labels here also have no leading digits, so that trap doesn't apply.
