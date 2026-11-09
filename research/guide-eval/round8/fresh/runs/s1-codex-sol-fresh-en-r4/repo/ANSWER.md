# HR range fix

Changed `gen.py` so each `hr_pct` corridor is emitted as `hr: {"units": "%lthr", "start": low, "end": high}`. It previously used `value` for the lower bound. In Intervals.icu workout documents, `value` denotes a single target; a range uses `start` and `end`. The old shape could therefore be exported as a zone target instead of the planned corridor. The workout document now also declares `target: "HR"` so the exporter selects heart rate as the workout target.

The plan remains in percentages of the athlete's LTHR, so Intervals.icu can resolve those bounds using its configured LTHR (172 bpm in the readback). No watch zones or fixed bpm values are baked into the generator. The sample plan should resolve to approximately 117–129, 151–160, 129–141, and 112–124 bpm, respectively, subject to Intervals.icu's rounding.

I checked the generated event locally, including both steps inside the repeat block. I did not push a new event or check a watch readback, so the device display still needs confirmation after a normal sync.

Reference: [Intervals.icu forum example of a workout document using `target: "HR"` and `hr: {"start", "end", "units"}`](https://forum.intervals.icu/t/hr-target-workouts-broken-on-edge-840-firmware-30-18-interpreted-as-hrmax-instead-of-bpm/130090).
