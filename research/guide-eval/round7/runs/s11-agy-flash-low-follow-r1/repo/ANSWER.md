# Cause and Fix: Second Publish 500 Error

## Cause

1. **DynamoDB Rejects Python Floats**:
   Boto3 / DynamoDB serializers do not support native Python `float` values, requiring `int` or `decimal.Decimal` instead (as evidenced by `TypeError: Float types are not supported. Use Decimal types instead` in `logs/error.log`).

2. **Why the First Publish Succeeded**:
   When the table was completely empty, `table.scan()` returned no items (`[]`). Consequently, `related(story, existing)` returned an empty list `[]`. No similarity scores were calculated or stored in `item["similar"]`, so no float attributes existed during the first `table.put_item()` call.

3. **Why the Second Publish Failed**:
   On the second publish, the table already contained the first item. The state-dependent similarity code path executed: `similarity(story, other)` computed the similarity score using `round(0.7 * tag_score + 0.3 * word_score, 4)`, returning a Python `float`. This float was stored under `item["similar"][i]["score"]`, causing `table.put_item(Item=item)` to fail with a `TypeError`, which `handler()` caught and returned as HTTP 500.

---

## Fix

1. **Code Fix (`src/app.py`)**:
   Updated `similarity()` in [src/app.py](file:///tmp/h-10mOYE/src/app.py) to return integer percentages instead of floating-point numbers:
   ```python
   return round(100 * (0.7 * tag_score + 0.3 * word_score))
   ```
   In Python 3, `round(x)` without a precision argument returns an `int`, which DynamoDB safely accepts.

2. **Test Fix (`tests/test_publish.py`)**:
   Added integration tests in [tests/test_publish.py](file:///tmp/h-10mOYE/tests/test_publish.py) that seed the table with an existing story before publishing a second one:
   - `test_publish_with_seeded_table_computes_similarity`: Verifies that publishing to a seeded table executes the similarity calculation path, successfully writes to the table, and stores integer scores.
   - `test_handler_publish_twice`: Verifies end-to-end `POST /stories` handling across multiple consecutive publishes.
