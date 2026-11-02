# Cause and Fix for Second Publish 500 Error

## Cause

When the first story is published to an empty DynamoDB table:
- `table.scan()` returns zero existing items (`Items: []`).
- `related(story, existing)` returns an empty list `[]`.
- `similar` attribute is `[]`, so no similarity calculation results are serialized into DynamoDB. The first publish succeeds (`201 Created`).

When a second story is published:
- `existing` now contains the first story.
- `related(story, existing)` calls `similarity(story, other)`.
- `similarity(...)` returned a Python `float` (`round(0.7 * tag_score + 0.3 * word_score, 4)`).
- DynamoDB's boto3 serializer explicitly disallows Python `float` values, raising:
  `TypeError: Float types are not supported. Use Decimal types instead.`
- This unhandled exception caused `handler()` to log an error and return HTTP `500 Internal Server Error`.

The original unit tests passed because they only tested publishing to an empty table, never executing the code path where `similar` has items with computed scores.

---

## Fix

1. **Convert similarity scores to `Decimal` in [src/app.py](file:///private/tmp/h-DvV9Z2/src/app.py):**
   - Imported `from decimal import Decimal`.
   - Updated `similarity(a, b)` to wrap the rounded float score in `Decimal(str(...))` before returning it, ensuring DynamoDB serialization accepts the value.

2. **Add integration / populated-table tests in [tests/test_publish.py](file:///private/tmp/h-DvV9Z2/tests/test_publish.py):**
   - Added tests (`test_second_publish_stores_similar_stories_without_float_error` and `test_handler_second_publish_succeeds`) that seed an initial item and publish a second item.
   - These tests verify that the similarity score serialization and handler succeed on populated tables, ensuring the regression cannot come back.
