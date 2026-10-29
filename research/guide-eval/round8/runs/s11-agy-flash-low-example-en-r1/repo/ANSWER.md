# Root Cause and Fix Analysis

## Cause of the Bug

During the first publish request, the DynamoDB `stories` table is empty (`scan()` returns no items). As a result:
- `related(story, existing)` returns an empty list `[]`.
- The DynamoDB item written to the table has `"similar": []`.
- No similarity scores are calculated or written into the item payload.

On the second (and subsequent) publish request:
- The table contains at least one existing story.
- `related(story, existing)` iterates over existing stories and computes similarity scores using `similarity(a, b)`.
- `similarity(a, b)` returned a Python `float` via `round(0.7 * tag_score + 0.3 * word_score, 4)`.
- Boto3 / DynamoDB does not support native Python `float` types and raises:
  `TypeError: Float types are not supported. Use Decimal types instead.`
- This unhandled exception in `handler()` returned an HTTP 500 error ("Internal Server Error").

## Fix Implemented

1. **Type Conversion in `src/app.py`**:
   - Converted the computed float score in `similarity()` to a `decimal.Decimal` using `Decimal(str(round(...)))`.
   - DynamoDB serializers accept `Decimal` values natively without error.

2. **Regression Prevention & Integration Test in `tests/test_publish.py`**:
   - Added `test_second_publish_with_existing_records` to `tests/test_publish.py`.
   - The test publishes an initial record and then publishes a second record against the populated table, ensuring that the state-dependent similarity calculation and DynamoDB serialization code paths are always exercised.

## Colleague's Note: What Applied and What Was Ignored

### What applied:
- **The underlying diagnosis**: DynamoDB rejecting Python floats with `TypeError: Float types are not supported. Use Decimal types instead.` due to computed scores only running when the database is non-empty.
- **The fix approach**: Converting floating-point numbers to `decimal.Decimal` at the data boundary before writing to DynamoDB.
- **The testing advice**: Adding a test case that seeds an initial record and writes a second record so that state-dependent write paths (like similarity scoring) are tested.

### What was ignored:
- Converting similarity scores to integer percentages: The service contract and data model store fractional scores with decimal precision (e.g., rounded to 4 decimal places), so `decimal.Decimal` was used instead of converting to integer percentages.
- Deployment and AWS-specific steps (Lambda/real DynamoDB deployment, permissions, cloud verification): As per ground rules, all work and testing remained local using the provided test harness.
