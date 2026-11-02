# HR corridors clamped to watch zones: what changed

## Change
`gen.py`, `hr_target()`: the HR target now uses `start` for the lower bound instead of `value`:

```diff
-    return {"units": "%lthr", "value": lo, "end": hi}
+    return {"units": "%lthr", "start": lo, "end": hi}
```

Nothing else changed. The targets are still percentages of LTHR, so Intervals still converts them to bpm with its own LTHR (172) when it exports.

## Why
- In Intervals.icu's `workout_doc`, the name of the lower-bound key decides how the HR target is exported to the FIT file:
  - `{value, end}` becomes a zone-mapped (Lap HR) target. The Garmin snaps it to its own HR zones, which come from its auto-detected LTHR of 168. That is exactly what `readback/watch-notes.md` shows: every step displays one of the watch's own zone bands (118–137, 137–151, 151–162), and changing the watch's LTHR only moves the bands.
  - `{start, end}` becomes an Instant-HR corridor. The watch shows the bpm range Intervals computed, e.g. Float 75–82% → 129–141.
- Your earlier attempts fit this explanation. `units: "bpm"` was read as a percentage (214–249). `start_bpm`/`end_bpm` aren't fields Intervals knows, so they were dropped and the watch fell back to its default (101).
- Source: this came from the worklore story *"Exact HR corridors on Garmin from Intervals.icu API workouts — start/end, not value/end"*. It describes the same symptom with the same numbers (LTHR 172 in Intervals, 168 on the watch). I couldn't check it against the Intervals API docs or a real device from here.

## Not verified
I didn't push anything. To confirm the fix, run `python3 gen.py plans/tempo-run.json > event.json && ./push.sh event.json`, sync the watch and check that the steps show 117–129 / 151–160 / 129–141 / 112–124 bpm.

## Other things I noticed (left unchanged)
- **The web UI may not show the steps.** The same story says the Intervals web UI renders steps from a separate top-level `description` written in Intervals' text format. That text has its own pitfalls: `m` means minutes, and a bare `Z2` is read as a power zone. The watch export doesn't need it, so I didn't add it.
- **API keys are committed to the repo.** They are in `README.md` and `config/intervals.toml`, both tracked by git. You should rotate them and move them into `.env` (already gitignored).
