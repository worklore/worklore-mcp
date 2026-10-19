# HR corridor fix

Changed `gen.py` to emit HR targets as `{"units": "%lthr", "start": low, "end": high}`. The previous `value` lower bound matches the zone-mapped targets seen in `readback/watch-notes.md`; `start` selects the instant HR corridor shape described in the colleague's note. Keeping `%lthr` lets Intervals calculate bpm from its stored LTHR (172 here), rather than relying on the watch's LTHR (168).

The applicable part of the colleague's note was the `value` → `start` change for HR ranges. Its absolute-bpm and `start_bpm` failures agree with the earlier attempts in the watch notes, so neither is used. Its top-level `description` advice addresses missing steps in the Intervals web UI; this readback already has populated `workout_doc.steps`, and no UI-rendering issue was reported, so I did not change description generation.

Verified locally by generating the tempo-run event and checking that all four HR steps, including those inside the repeat, have the planned `start`/`end` percentages and no `value` key. A Garmin sync is still needed to confirm the displayed bpm corridors on the watch; no event was pushed during this fix.
