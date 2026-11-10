## Cause

The `similarity()` function in `src/app.py` returns a Python `float` from `round(0.7 * tag_score + 0.3 * word_score, 4)`. This float is stored in the `similar` array as the `score` field of related stories.

The first publish succeeds because the DynamoDB table is empty: `related()` returns an empty list, so no scores (and no floats) are written to the item. Once a story exists in the table, the second publish calls `related()`, which computes similarity scores as floats and includes them in the item passed to `table.put_item()`. DynamoDB rejects float types — it only accepts `Decimal`, `int`, `str`, `bool`, `bytes`, or `None`. This causes the `TypeError: Float types are not supported. Use Decimal types instead.` error seen in `logs/error.log`.

This matches the colleague's note: the empty-database path hid the bug, and the populated-table path exposed it.

## Fix

1. **Code fix (src/app.py):**
   - Added `from decimal import Decimal` import
   - Changed `similarity()` to return `Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))` instead of a raw float
   - This converts the rounded float to a string, then to a `Decimal`, which DynamoDB accepts

2. **Test fix (tests/test_publish.py):**
   - Seeded the fake table with an existing story before publishing the test story
   - This ensures the test exercises the populated-table path where similarity scores are computed
   - The test now catches the bug if floats are ever reintroduced

## Parts of the colleague's note that applied

- The empty-database path hiding the bug: **applied** — first publish worked, second failed
- The scoring path producing floats that DynamoDB rejects: **applied** — `similarity()` returned floats
- The fix of changing float scores to a DynamoDB-compatible type: **applied** — used `Decimal` instead of `int` (which would lose precision)
- The test change to seed the table: **applied** — test now pre-populates with one story

The colleague's note described the exact same issue and solution approach. The only difference is that we used `Decimal` (preserving the fractional scores) rather than integer percentages, since the similarity computation produces values in the range [0, 1] with 4 decimal places of precision.
