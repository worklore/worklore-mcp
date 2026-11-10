## Cause

The `similarity()` function in `src/app.py` returns a Python `float` (from `round(...)`). This float is stored in the `similar` list as the `score` field of each related story. When `publish()` writes the item to DynamoDB via `table.put_item(Item=item)`, DynamoDB rejects the float type with:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

The first publish succeeds because the table is empty: `related()` returns an empty list, so no scores are written. Once the table contains at least one story, `similarity()` is invoked, producing float scores that reach the write path, causing the 500 error.

## Fix

Changed `similarity()` to return an integer percentage instead of a float:

```python
# Before:
return round(0.7 * tag_score + 0.3 * word_score, 4)

# After:
return int(round((0.7 * tag_score + 0.3 * word_score) * 100))
```

This converts the similarity score to an integer percentage (0-100), which DynamoDB accepts.

Also updated the test in `tests/test_publish.py` to seed the table with one story before testing the write, ensuring the populated-table path is exercised and this class of bug cannot hide in the empty-table path again.

## Colleague's Note - What Applied

The colleague's note described the exact same issue: floats being passed to DynamoDB writes, with the empty-database path hiding the bug. The following parts applied:

- "TypeError: Float types are not supported. Use Decimal types instead." - Same error message
- "The first publish succeeded because the table was empty: there were no matches, so there were no scores or floats to write." - Same root cause
- "Once the table contained a story, the scoring path ran and passed Python floats to DynamoDB, which did not accept them." - Same failure mode
- "The empty-table path had hidden the bug until the data existed." - Same testing gap
- "I fixed it with a one-line change that made the scores integer percentages." - Same fix approach
- "I also changed every write-path test to seed the table with one record before testing the write, so the populated-table path actually ran." - Same test improvement
