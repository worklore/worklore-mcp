# Generator fix

`gen.py` now writes HR corridors as `{"units": "%lthr", "start": low, "end": high}`. Intervals uses `start`/`end` for an Instant HR corridor; the previous `value`/`end` shape exported as a zone-mapped target, which explains the watch bands in `readback/watch-notes.md`. Percentages remain relative to the LTHR stored in Intervals, so the sample Float target should export as about 129–141 bpm from LTHR 172.

The event also includes a top-level `description` in Intervals' workout text grammar. It lists each step, uses `m` for minutes, and places blank lines around repeat blocks so the web UI can parse and display the workout. Labels starting with digits or containing `Z` followed by a number are made safe for that grammar in the description; the structured step labels remain as supplied.

Local verification: generated `plans/tempo-run.json` and checked that all four HR steps use `%lthr` with `start`/`end`, that the description contains the `3x` Tempo/Float block, and that the Python file compiles. No event was sent to Intervals or synced to a watch, so API parsing and Garmin display still require a real round trip to confirm.
