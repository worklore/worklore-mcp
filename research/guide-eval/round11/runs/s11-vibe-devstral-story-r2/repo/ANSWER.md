# Cause and Fix for Second Publish 500 Error

## Cause

The `similarity()` function in `src/app.py` computes similarity scores using floating-point division (`/`). The result is rounded to 4 decimal places with `round()`, which returns a Python `float`. These float scores are stored in the `similar` list, which is part of the DynamoDB item.

DynamoDB (via boto3) rejects float types — it only accepts `int`, `str`, `bytes`, `bool`, `None`, or `Decimal`. The error message in `logs/error.log` confirms this:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The first publish succeeds because the table is empty — `related()` returns an empty list, so `similarity()` is never called and no float scores are produced. The second publish fails because there is now an existing story, so `similarity()` is invoked, producing float scores that DynamoDB rejects.

## Fix

Changed `src/app.py` line 24:

**Before:**
```python
return round(0.7 * tag_score + 0.3 * word_score, 4)
```

**After:**
```python
return int(round((0.7 * tag_score + 0.3 * word_score) * 10000))
```

This converts the float score to an integer by scaling it by 10000 (preserving 4 decimal places of precision as an integer). DynamoDB accepts integers, so the write succeeds.

Also added a test in `tests/test_publish.py` (`test_publish_with_existing_story`) that seeds the table with one story before publishing a second one. This exercises the state-dependent code path (similarity scoring) that the original test never touched.

## Parts of the colleague's note that applied

- **"DynamoDB does not accept Python floats"** — Directly matches our error.
- **"the first write survived... the table was empty — no matches, no scores, no floats, no crash"** — Exactly our situation: first publish works, second fails when data exists.
- **"the bug did not exist until the data did"** — The float issue only manifests when there are existing stories to compute similarity against.
- **"Any code whose behavior depends on existing state... has a second code path that first-write tests never touch"** — The `related()` function with similarity scoring is the state-dependent path.
- **"convert to int or decimal.Decimal at the boundary"** — We converted to int at the DynamoDB boundary.
- **"add one integration test that seeds a record and writes a second one"** — Added `test_publish_with_existing_story` that does exactly this.

Parts that did NOT apply:
- The colleague used integer percentages; we preserved 4 decimal places by scaling to an integer (e.g., 0.8765 becomes 8765).
- The colleague's fix was "one line" — ours required the same code fix plus a test addition.
