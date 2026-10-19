# HR range fix

Changed `gen.py` to encode each planned HR corridor as `hr: {"start": low, "end": high, "units": "%lthr"}` and set `workout_doc.target` to `"HR"`.

The old object put the lower bound in `value`, which denotes a single target, while `end` alone did not define a range. It also left the workout target selection implicit. The watch readback showed zone bands instead of the intended bounds. Explicit `start` and `end` preserve the planned percentage corridor, and `target: "HR"` selects heart rate for the workout.

Verified locally that all four generated step types retain their planned bounds, including steps inside the repeat block. Watch behavior still requires a fresh sync to confirm; no external service was contacted for testing.
