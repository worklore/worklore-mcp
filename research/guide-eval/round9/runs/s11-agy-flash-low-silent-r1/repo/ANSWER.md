# Postmortem: Second Publish 500 Error

## Cause

When the first story was published (`why-my-cron-ran-twice`), the DynamoDB table was empty. As a result:
- `table.scan()` returned no items (`existing = []`).
- `related(story, existing)` returned an empty list (`similar = []`).
- No similarity score calculations were performed, so the item contained only strings, lists of strings, and integer timestamps, which DynamoDB / `boto3` accepts.

When the second story was published:
- `table.scan()` returned the previously published story.
- `related(story, existing)` evaluated `similarity(story, other)`.
- `similarity()` computed floating-point numbers (`round(0.7 * tag_score + 0.3 * word_score, 4)`).
- When `table.put_item(Item=item)` was called, `boto3`'s DynamoDB serializer rejected the Python `float` with:
  `TypeError: Float types are not supported. Use Decimal types instead.`
- This uncaught `TypeError` was caught by `handler()`'s broad `except Exception:` block and logged as `ERROR stories publish failed` returning HTTP 500.

---

## Fix

1. **Convert similarity scores to `Decimal`**:
   In `src/app.py`, imported `Decimal` from Python's standard `decimal` module and converted the calculated score in `similarity()` using `Decimal(str(round(...)))`. DynamoDB requires decimal numbers to be passed as `Decimal` instances.
2. **Added regression test**:
   In `tests/test_publish.py`, added `test_publish_second_story_succeeds_with_similarity_scores` to verify publishing a second story when existing stories are present in the table, ensuring similarity calculations and storage succeed without type serialization errors.
