# HR targets clamped to watch zones — fix

## Cause

`gen.py` emitted HR targets as `{"units": "%lthr", "value": lo, "end": hi}` and
left the conversion to Intervals.icu at export. The export to Garmin then
mapped those percentages onto the watch's own zone bands, so every corridor
showed up as a zone edge (118–137, 137–151, …) rather than the planned range.
Changing the watch's LTHR only moved the bands.

## Change (`gen.py`)

- Added `LTHR = 172` (the athlete's LTHR, per README.md) with a comment on why.
- `hr_target()` now converts each plan percentage to absolute bpm:
  `start = round(172 * lo / 100)`, `end = round(172 * hi / 100)`, with
  `"units": "bpm"`.
- The `hr` key names changed from `value`/`end` to `start`/`end`, which is the
  form the Intervals forum shows for bpm HR targets.

Generated targets for `plans/tempo-run.json`:

| step | planned (% LTHR) | generated (bpm) | matches watch-notes "expected" |
|---|---|---|---|
| Warm-up easy | 68–75 | 117–129 | yes |
| Tempo | 88–93 | 151–160 | yes |
| Float | 75–82 | 129–141 | yes |
| Cool-down | 65–72 | 112–124 | yes |

## Not verified

- **Not pushed.** I did not POST anything to Intervals. `readback/` still holds
  the old `%lthr` payload for event 184233.
- **Not checked on the watch.** I have no device access. The `start`/`end` +
  `bpm` shape comes from a forum bug report, not the official API schema, so
  it needs one push to a test event and a look at the Forerunner before
  trusting it.
- **Earlier bpm attempt.** The notes say `units: "bpm"` with absolute values
  once showed 214–249 bpm. I don't know which keys or values that attempt used,
  so I can't rule out the same problem. If the watch shows wrong numbers again,
  check the exact payload that was sent and whether the Garmin export treats
  bpm targets as % of max HR (a known problem on some Garmin firmware).
- **LTHR is hard-coded.** If the athlete's LTHR changes in Intervals, update
  `LTHR` in `gen.py` too.

## Next step

Push the regenerated event (`python3 gen.py plans/tempo-run.json > event.json`,
then `./push.sh event.json`) to a test athlete or test date, then compare the
watch display with the table above.
