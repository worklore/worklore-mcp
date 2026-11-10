## Cause

The `similarity()` function in `src/app.py` returns a Python `float` (via `round()`). When a second story is published, the `related()` function calls `similarity()` to compute scores between the new story and existing stories, storing these float values in the `similar` list as `{"slug": ..., "score": <float>}`. When `publish()` calls `table.put_item(Item=item)`, DynamoDB rejects the float type with: `TypeError: Float types are not supported. Use Decimal types instead.`

The first publish succeeds because the table is empty, so `related()` returns an empty list and no scores are computed. Once the table contains at least one story, the scoring path runs and passes Python floats to DynamoDB.

## Fix

Changed `similarity()` in `src/app.py` to return an integer percentage (0-100) instead of a float (0.0-1.0):

```python
# Before:
return round(0.7 * tag_score + 0.3 * word_score, 4)

# After:
return int(round((0.7 * tag_score + 0.3 * word_score) * 100))
```

DynamoDB accepts integers. Also added a test case `test_publish_with_existing_story` that seeds the table with one record before publishing, ensuring the populated-table path is exercised.

## What from the colleague's note applied

- The exact error message: "TypeError: Float types are not supported. Use Decimal types instead."
- The root cause: floats from scoring logic being passed to DynamoDB
- The empty-database path hiding the bug on first publish
- The fix approach: converting floats to integers (we used integer percentages instead of Decimals)
- The test improvement: seeding the table before testing writes to exercise the populated-table path
