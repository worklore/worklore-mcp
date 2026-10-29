# Answer

## What was changed
1. **Added a constant `LTHR`** (172 bpm) after the imports.
2. **Reimplemented `hr_target`**:
   - Previously returned a corridor expressed as a percentage of LTHR:
     ```python
     return {"units": "%lthr", "value": lo, "end": hi}
     ```
   - Now converts the percentage range to absolute BPM using the constant LTHR and returns the corridor with `units: "bpm"`:
     ```python
     lo_pct, hi_pct = step["hr_pct"]
     lo_bpm = int(round(lo_pct / 100.0 * LTHR))
     hi_bpm = int(round(hi_pct / 100.0 * LTHR))
     return {"units": "bpm", "value": lo_bpm, "end": hi_bpm}
     ```
3. Cleaned duplicate `LTHR` definitions and added a comment explaining its purpose.

## Why it was changed
- The watch displays heart‑rate zones based on the **absolute BPM values** it receives. When the generator emitted percentages (`%lthr`), the watch mapped them onto its own predefined zones, resulting in the truncated ranges shown in `readback/watch‑notes.md`.
- Converting the planned percentage ranges to absolute BPM using the athlete’s LTHR (172 bpm, as observed in the notes) ensures the watch shows the exact ranges we intended (e.g., 151‑160 bpm instead of generic “Z4”).
- Adding the `LTHR` constant makes the conversion deterministic and easy to adjust for a different athlete.

**Result:** The generated `workout_doc` now contains heart‑rate corridors in BPM, so the watch displays the correct, un‑truncated ranges matching the plan.
