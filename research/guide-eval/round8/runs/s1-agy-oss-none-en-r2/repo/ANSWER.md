# Answer

## What was changed

- **File:** `gen.py`
- **Function:** `hr_target`
- **Modification:** Updated the returned dictionary from:
  ```python
  return {"units": "%lthr", "value": lo, "end": hi}
  ```
  to:
  ```python
  return {"units": "%lthr", "start": lo, "end": hi}
  ```

## Why the change fixes the issue

The watch displays HR zones based on the athlete’s own zone definitions. The Intervals.icu JSON schema for a heart‑rate corridor expressed as a percentage of LTHR expects the keys **`start`** and **`end`** to define the lower and upper bounds of the range. Using the key **`value`** signals a single flat target, which causes the watch to interpret the corridor as a zone edge rather than the intended range. By returning `{ "units": "%lthr", "start": lo, "end": hi }`, the generated workout now correctly represents a corridor, and the watch will display the exact percentage range we planned (e.g., 151–160 % LTHR) instead of clamping to its internal zones.

---

*All changes were made within the current workspace directory as requested. No external services were contacted.*