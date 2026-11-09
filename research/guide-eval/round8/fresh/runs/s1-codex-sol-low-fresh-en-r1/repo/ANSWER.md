# Generator fix

`gen.py` now emits Intervals.icu workout text in the event's `description` field, using explicit `% LTHR` corridors and `Nx` repeat blocks. It no longer sends a hand-built `workout_doc`.

The old payload was accepted and returned unchanged, but that only confirmed storage. The watch readback showed zone-edge targets instead of the planned ranges. Intervals' current API export path parses the workout description for device sync; a stored `workout_doc` alone is not a reliable source for that export. The new text uses Intervals' range syntax, such as `- 8m 88-93% LTHR Tempo`, so Intervals can resolve each corridor against the athlete's LTHR of 172 rather than the watch's zones. Using `bpm` directly is also unsuitable: the prior attempt produced implausible values on the watch.

Local check: generating `plans/tempo-run.json` produces the four planned HR corridors and the three-repeat block in `description`, with no `workout_doc`. No event was pushed or watch sync performed, so the watch display still needs a fresh event for confirmation.
