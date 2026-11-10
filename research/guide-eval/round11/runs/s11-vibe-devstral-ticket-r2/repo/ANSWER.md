## Cause

The `similarity()` function in `src/app.py` returns a Python `float` (rounded to 4 decimal places). This float is stored in the `similar` list as the `score` field for each related story. When `publish()` writes the item to DynamoDB via `table.put_item(Item=item)`, DynamoDB rejects the float type with: `TypeError: Float types are not supported. Use Decimal types instead.`

The first publish succeeds because the table is empty: `related()` returns an empty list, so no scores (and no floats) are written. Once a story exists in the table, the second publish computes similarity scores and includes float values in the item, triggering the error.

This matches the colleague's note: the empty-database path hid the bug, and the scoring logic had a path that depended on existing state (the populated-table path).

## Fix

**app.py line 37**: Changed the score from a float to an integer percentage by multiplying by 100 and rounding:

```python
# Before:
scored.append({"slug": other["slug"], "score": similarity(story, other)})

# After:
scored.append({"slug": other["slug"], "score": int(round(similarity(story, other) * 100))})
```

DynamoDB accepts integers, so this eliminates the float-type error. The score is now stored as an integer percentage (e.g., 75 instead of 0.75), which preserves the ordering while being compatible with DynamoDB.

**tests/test_publish.py**: Added `test_publish_with_existing_story` that seeds the table with one record before publishing, ensuring the populated-table path is tested. This prevents the bug from being hidden by empty-table tests.

## Parts of the colleague's note that applied

- The empty-database path hiding the bug: **applied** — first publish worked, second failed
- Float types from scoring reaching the write: **applied** — similarity() returned floats that DynamoDB rejected
- Fix by changing floats to integers: **applied** — converted scores to integer percentages
- Seeding tests with existing data: **applied** — added test that pre-populates the table

## Parts that did not apply

- Using Decimal types: not needed — integers are sufficient and simpler
- Division/average/rounded scores in item dictionaries: the only path was through the `similar` list's `score` field
