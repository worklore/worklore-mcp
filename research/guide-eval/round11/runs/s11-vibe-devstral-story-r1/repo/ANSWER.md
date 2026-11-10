# Cause and Fix for Second Publish 500 Error

## Cause

The `similarity()` function in `src/app.py` returns a Python `float` via `round(0.7 * tag_score + 0.3 * word_score, 4)`. DynamoDB does not accept float types - it requires `Decimal` or numeric types like `int`.

The first publish succeeds because the table is empty: `related()` returns an empty list, so no similarity scores are computed, and no floats are passed to `put_item()`. The second publish fails because there is now one existing story, `similarity()` is called, a float score is stored in the `similar` list, and `put_item()` rejects it with `TypeError: Float types are not supported. Use Decimal types instead.`

This matches the colleague's note exactly: "my API computes similarity scores... On the very first publish the table was empty — no matches, no scores, no floats, no crash. The bug did not exist until the data did."

## Fix

1. **Code fix** (`src/app.py`):
   - Added `from decimal import Decimal` import
   - Changed `similarity()` to return `Decimal(str(round(...)))` instead of a raw float
   - This converts the float to a string first, then to Decimal, which DynamoDB accepts

2. **Test fix** (`tests/test_publish.py`):
   - Added `test_publish_with_existing_story` that seeds the table with one record before publishing a second story
   - This exercises the state-dependent code path (similarity computation with existing data)
   - The colleague's lesson applies: "the populated path is the real path; the empty path happens exactly once in production, ever"

## Parts of the colleague's note that applied

- The exact same error message: `TypeError: Float types are not supported. Use Decimal types instead.`
- The same root cause: float values from similarity scoring being passed to DynamoDB
- The same pattern: first write works (empty table), second write fails (table has data)
- The same fix approach: convert floats to Decimal at the boundary
- The same test approach: seed the table with one record before testing the second write
