# ANSWER

## The fix

One-word change in `hr_target` (`gen.py:13`): the lower bound of each HR
corridor is now `"start"` instead of `"value"`, so every step target is
`{"units": "%lthr", "start": <low>, "end": <high>}` instead of
`{"units": "%lthr", "value": <low>, "end": <high>}`.

## Why

The key that names the corridor's lower bound selects how Intervals' FIT
export encodes the target:

- `value` + `end` routes as a **lap-HR / zone-mapped** target. The watch
  ignores the numbers and clamps the corridor to the edges of its own
  (auto-detected, stale) HR zones.
- `start` + `end` routes as an **instant-HR corridor**, and the watch
  displays the raw bpm Intervals computed from its stored thresholds.

The evidence in `readback/watch-notes.md` matches the zone-clamping mode
exactly: every displayed corridor is a watch zone band (118–137 = Z2,
151–162 = Z4, 137–151 = Z3), never the planned range × Intervals' LTHR
172 (117–129, 151–160, 129–141, 112–124). Changing the watch's LTHR
moved the bands but they stayed zone edges — the watch was mapping our
target into its own zones, which is the signature of the `value`/`end`
shape. With `start`/`end`, the watch will show Intervals' computed bpm
(from its LTHR 172), immune to the watch's own zone table.

Verified locally: `python3 gen.py plans/tempo-run.json` now emits
`"start"`/`"end"` for all four HR targets. Pushing to Intervals / syncing
the watch was not done from here (no external calls per ground rules), so
end-to-end watch confirmation still needs the normal push → sync → check.

## Which parts of the colleague's note applied

Applied:

- **The breakthrough** — the corridor's lower bound must be `start`, not
  `value`; that one key switches the FIT export from zone-mapped to
  instant-HR. This was the whole fix.
- **Percentages, not absolute bpm** — keep `units: "%lthr"` and let
  Intervals convert from its own stored threshold at export time. We were
  already doing this; kept, because it keeps the corridor correct even
  when the watch's LTHR differs from Intervals'.
- **Do not use `units: "bpm"` with absolute values** — consistent with our
  own earlier failure (watch showed impossible 214–249 bpm); reinforced
  the decision to stay on `%lthr`.
- **Do not use `start_bpm`/`end_bpm`** — consistent with our earlier
  failure (constant 101 fallback, silently dropped by the schema).

Considered but not applied:

- **The top-level `description` text-grammar trap** (the "bonus trap":
  `m` = minutes, `mtr`/`km` for distance, blank lines around `Nx` blocks,
  no leading digits in labels, and a choked parser wipes both
  representations). Not applied, because (a) it fixes step rendering in
  the Intervals web UI, a different symptom from the watch clamping we
  reported — our readback shows `workout_doc.steps` populated, so the API
  side is fine; (b) we can't verify a generated grammar against the live
  parser from here, and per the note a malformed description can wipe the
  workout entirely — adding unverifiable risk to fix an unobserved
  problem. Worth revisiting separately if UI visibility becomes a need.
- **The UI-dropdown / "absolute bpm is impossible" misdiagnosis** — only
  explained the colleague's earlier wrong turn; nothing to act on since
  we target the API with `%lthr`.
