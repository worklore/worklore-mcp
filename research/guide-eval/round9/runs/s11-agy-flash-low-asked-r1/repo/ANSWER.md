# Publishing 500 Error Analysis & Fix

## Cause
When a story is published, `publish()` calculates similarity scores between the incoming story and existing stories via `similarity(a, b)`:
```python
def similarity(a, b):
    ...
    return round(0.7 * tag_score + 0.3 * word_score, 4)
```
In Python, `round(...)` with float arguments returns a Python `float`.

- On the **first publish**, the DynamoDB table is empty (`existing` items = `[]`). The `related()` function iterates over `existing`, finds no other stories, and returns an empty list `[]` for `similar`. No similarity calculation is stored, so `table.put_item(Item=item)` succeeds.
- On the **second publish**, the table contains the first published story. `related()` computes similarity scores as Python `float` values and populates `item["similar"] = [{"slug": ..., "score": <float>}]`.
- When `table.put_item(Item=item)` is called, boto3's DynamoDB serializer raises:
  ```
  TypeError: Float types are not supported. Use Decimal types instead.
  ```
- Because `handler()` catches unexpected exceptions and logs them before returning a 500 status code, the second publish returns HTTP 500.

The unit tests previously missed this because `PublishTest` only tested publishing a single story into an empty table.

## Fix
1. **Source Fix (`src/app.py`)**:
   Import `Decimal` from Python's standard `decimal` module and wrap the rounded similarity score in `Decimal(str(...))` so the score stored in DynamoDB is a `Decimal` instead of a `float`:
   ```python
   from decimal import Decimal
   ...
   return Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))
   ```

2. **Regression Prevention / Tests (`tests/test_publish.py`)**:
   Added tests that execute the populated-table path:
   - `test_publish_second_story_succeeds_with_similarity`: Verifies that publishing a second story computes and stores related similarity items in DynamoDB without type errors.
   - `test_handler_second_publish`: Verifies end-to-end `handler` execution across consecutive publishes returning HTTP 201.
