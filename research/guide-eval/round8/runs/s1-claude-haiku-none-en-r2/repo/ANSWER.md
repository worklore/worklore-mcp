# HR ranges clamped to watch zones — fix

## Cause

`gen.py` emitted each HR target as `{"units": "%lthr", "value": lo, "end": hi}`
and left the conversion to Intervals/Garmin. The watch auto-detects its own
LTHR (168 here, not 172), and the %LTHR targets reach it as its own zone
bands, so every corridor came back as a zone edge (118–137, 137–151, 151–162)
instead of the planned bpm range.

## Change (`gen.py`)

- Added an `LTHR = 172` constant and a `pct_to_bpm()` helper that rounds
  `pct * LTHR / 100` to the nearest bpm using integer math.
- `hr_target()` now emits `{"units": "bpm", "value": <lo bpm>, "end": <hi bpm>}`.
- Kept the `value`/`end` keys and the rest of the document structure unchanged,
  since the API already accepted that shape (`readback/event-184233-as-sent.json`).

## Result for `plans/tempo-run.json`

Checked by running `gen.py` and reading the targets back:

| step | planned (% LTHR) | emitted (bpm) | expected on watch (from notes) |
|---|---|---|---|
| Warm-up easy | 68–75 | 117–129 | 117–129 |
| Tempo | 88–93 | 151–160 | 151–160 |
| Float | 75–82 | 129–141 | 129–141 |
| Cool-down | 65–72 | 112–124 | 112–124 |

Rounding: 0.68×172 = 116.96 → 117, 0.93×172 = 159.96 → 160, and so on.

## Not verified

- I have not pushed the event or checked it on the watch. The ground rules
  rule out reporting to external services, and I have no API key here. The fix
  is based on the readback notes plus the arithmetic above, not on a live
  re-test.
- The notes say an earlier `units: "bpm"` attempt showed 214–249 bpm. I can't
  reproduce that from the repo, and nothing here explains it. If the new payload
  still shows wrong numbers, compare it with that earlier payload first.
- If the watch later changes LTHR, the bpm values will not follow it. That is
  the trade-off for pinning the corridors; update `LTHR` in `gen.py` if the
  athlete's LTHR in Intervals changes.

## Files

- `gen.py` — LTHR constant, `pct_to_bpm()`, `hr_target()` now emits bpm.
- `README.md` — the line claiming Intervals converts %LTHR at export is replaced
  with the new behaviour.
