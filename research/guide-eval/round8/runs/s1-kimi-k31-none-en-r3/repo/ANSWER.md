# HR range fix

Changed `hr_target` in `gen.py` to emit `start` and `end` instead of `value` and `end`.

`value` represents a single target, so the watch export used the lower percentage to select one of its own heart-rate zones rather than preserving the planned corridor. `start` and `end` explicitly represent the lower and upper bounds of a range. The targets remain in `%lthr`; no BPM conversion or watch-specific zone values are needed.

For `plans/tempo-run.json`, the generated ranges are now:

- Warm-up easy: 68–75% LTHR
- Tempo: 88–93% LTHR
- Float: 75–82% LTHR
- Cool-down: 65–72% LTHR

Verified locally by running the generator and asserting all four HR target objects match those ranges. Nothing was deployed or sent to an external service, so watch display has not been re-tested.
