# HR range fix

Changed `gen.py` to encode each percentage-of-LTHR corridor as `hr.start` and `hr.end`. The old payload used `hr.value` for the lower bound. In the workout document format, `value` denotes a single target; a range uses `start` and `end`. That mismatch explains why the accepted event did not preserve the planned lower and upper bounds on the watch.

The generated tempo step now has `{"units":"%lthr","start":88,"end":93}`; the float has `start:75, end:82`. Keeping `%lthr` lets Intervals resolve the athlete's LTHR during export. I did not use absolute `bpm`, which the readback says produced incorrect targets.

Verified locally by generating `plans/tempo-run.json` and inspecting all four HR steps. Watch display still needs a new sync to confirm the exporter honors these ranges; no event was pushed.
