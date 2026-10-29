# Diagnosis and Fix: Second Publish 500 Error

## Cause

When the first story is published, the DynamoDB `stories` table is empty. The `related()` function scans the table, finds 0 existing items, and sets `"similar": []`. Because the list is empty, no similarity scores are stored in DynamoDB, and the write succeeds.

When a second story is published:
1. `table.scan()` returns the first story.
2. `related()` computes the similarity between the new story and existing stories using `similarity(story, other)`.
3. `similarity()` returned a Python standard `float` value (`round(0.7 * tag_score + 0.3 * word_score, 4)`).
4. `boto3`'s DynamoDB type serializer rejects Python `float` values with:
   ```
   TypeError: Float types are not supported. Use Decimal types instead.
   ```
5. `handler()` catches generic exceptions, logs `stories publish failed`, and returns HTTP `500`.

## Fix

1. **`src/app.py`**:
   - Imported `Decimal` from Python's standard `decimal` module.
   - Updated `similarity(a, b)` to return `Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))` instead of a `float`. DynamoDB serializers in `boto3` accept `Decimal` objects for numeric values.

2. **`tests/test_publish.py`**:
   - Added unit test coverage (`test_publish_second_story_with_similarity` and `test_handler_second_publish`) verifying that publishing subsequent stories calculates similarities and successfully saves items to DynamoDB without type serialization errors.
