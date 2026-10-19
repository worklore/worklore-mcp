# Changes and Rationale

## What Changed and Why

In `gen.py` (`hr_target`), changed the lower-bound key of the step HR target object from `"value"` to `"start"`:

```python
def hr_target(step):
    """HR corridor for a step, as a percentage of the athlete's LTHR."""
    lo, hi = step["hr_pct"]
    return {"units": "%lthr", "start": lo, "end": hi}
```

### Why

When `workout_doc.steps` specifies an HR target as `{"units": "%lthr", "value": lo, "end": hi}`, Intervals.icu FIT-exports the step as a **Lap-HR / zone-mapped** target. On the Garmin watch (Forerunner 965 with auto-detected LTHR 168), that causes every HR range to be clamped to the watch's own local HR zone boundaries (`118–137`, `151–162`, `137–151`) rather than the planned corridor.

Renaming `"value"` to `"start"` (`{"units": "%lthr", "start": lo, "end": hi}`) switches Intervals.icu's FIT export mode to an **Instant-HR corridor**. Intervals computes the exact bpm bounds from its own stored LTHR (172 bpm) at export time and sends the raw bpm range (`117–129`, `151–160`, `129–141`, `112–124`) to the watch, bypassing the watch's local zones.

---

## Which Parts of the Colleague's Note Applied

### Applied

1. **`start`/`end` vs. `value`/`end` key in `workout_doc.steps` HR targets (and Step 1's target schema):**
   - Directly applied. Using `{"units": "%lthr", "start": <low>, "end": <high>}` instead of `{"units": "%lthr", "value": <low>, "end": <high>}` is the exact fix needed in `gen.py` to export an Instant-HR corridor computed from Intervals' stored LTHR instead of a zone-clamped Lap-HR target.
2. **Explanation of failed `"bpm"` and `start_bpm`/`end_bpm` attempts:**
   - Applied as diagnostic confirmation. It explains the exact earlier failures noted in `readback/watch-notes.md` (`units: "bpm"` producing `214–249` bpm, and `start_bpm`/`end_bpm` producing a constant `101` fallback) and confirms that targets should remain percentages with `"units": "%lthr"`.

### Ignored (Did Not Apply)

1. **"Bonus trap" — top-level `description` in Intervals' text grammar (and Step 2 / Step 3 parser check):**
   - Ignored. `gen.py` constructs `workout_doc` directly without a top-level `description` field, and `readback/watch-notes.md` confirms that `GET /api/v1/athlete/{id}/events/184233` already returned `workout_doc.steps` populated as sent. The reported bug is strictly HR zone clamping on the watch, not missing steps in the Intervals web UI or text-parser edge cases (such as `m` vs. `mtr`/`km` distances, `Z2` swim power zones, or leading digits in labels).
2. **"Reproduce this" — live API requests, credential prompts, and Garmin Connect sync (Prerequisites, asking for athlete ID/API key, and live execution of Steps 1–4):**
   - Ignored. Fixing `gen.py` is purely local; we do not need athlete credentials, nor should we make live `POST`/`GET` requests to Intervals.icu or sync with Garmin Connect.
