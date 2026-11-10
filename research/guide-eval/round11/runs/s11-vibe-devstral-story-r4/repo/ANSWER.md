# Cause and Fix

## Cause

The `similarity()` function in `src/app.py` computes a score using floating-point division and returns a Python `float` via `round()`. DynamoDB (through boto3) rejects float types with the error: `TypeError: Float types are not supported. Use Decimal types instead.`

The first publish succeeds because the table is empty, so `related()` returns an empty list and no scores are stored. The second publish fails because there is now an existing story, so `similarity()` computes a float score which gets stored in the `similar` field of the DynamoDB item, triggering the error.

## Fix

1. **Code fix** (`src/app.py`):
   - Added `from decimal import Decimal` import
   - Changed `similarity()` to return `Decimal(str(round(...)))` instead of a raw float
   - This converts the computed float to a string and then to a Decimal, which DynamoDB accepts

2. **Test fix** (`tests/test_publish.py`):
   - Added `test_publish_with_existing_story()` that seeds the table with one story before publishing a second one
   - This exercises the state-dependent code path (the populated table path) that the original test never touched
   - Added assertion to verify the score is a Decimal type

## Which parts of the colleague's note applied

The following parts of the colleague's note applied directly:

- **The exact same error**: "TypeError: Float types are not supported. Use Decimal types instead."
- **The same pattern**: First write succeeds (empty table, no scores), second write fails (table has data, scores are computed as floats)
- **The same root cause**: Division operations producing Python floats that DynamoDB rejects
- **The same lesson**: Code whose behavior depends on existing state (similarity scoring) has a second code path that first-write tests never touch
- **The same fix strategy**: Convert computed values to Decimal at the boundary
- **The same test strategy**: Add an integration test that seeds a record and writes a second one, so state-dependent code actually executes under test

The colleague's note was essentially a perfect match for this exact problem.
