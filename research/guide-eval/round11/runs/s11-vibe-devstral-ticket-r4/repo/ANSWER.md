# Root Cause and Fix

## Cause

The `similarity()` function in `src/app.py` returns a Python `float` (via `round(..., 4)`). When a second story is published, the `related()` function computes similarity scores between the new story and existing stories, and these float values are placed into the `similar` list in the item dictionary. DynamoDB's boto3 serializer rejects Python float types with: `TypeError: Float types are not supported. Use Decimal types instead.`

The first publish succeeded because the table was empty, so `related()` returned an empty list and no scores were written. Once a story existed, the scoring path executed and the float values triggered the error.

This matches the colleague's note: the empty-database path hid the bug, and the populated-table path exposed it when computed floats reached the write.

## Fix

1. **Code change in `src/app.py`:**
   - Added `from decimal import Decimal` import
   - In `related()`, wrapped the similarity score in `Decimal(str(similarity(story, other)))` so DynamoDB receives a valid Decimal type instead of a Python float

2. **Test change in `tests/test_publish.py`:**
   - Added `test_publish_with_existing_story` that seeds the table with one story before publishing a second, ensuring the populated-table path is tested

## What from the colleague's note applied

- The exact error message: "TypeError: Float types are not supported. Use Decimal types instead."
- The pattern: first publish works (empty table), second fails (table has data)
- The root cause: computed floats reaching DynamoDB writes
- The fix strategy: convert floats to Decimal
- The test gap: empty-table tests missed the bug; need to seed with existing data

The colleague's note was directly applicable to this case.
