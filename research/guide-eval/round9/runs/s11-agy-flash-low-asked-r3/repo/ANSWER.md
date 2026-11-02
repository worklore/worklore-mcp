# Root Cause and Fix: Publishing Failure on Second Request

## Root Cause
On the first publish to an empty DynamoDB table, `table.scan()` returns no existing items (`similar: []`). Thus, no similarity calculation is stored.

On subsequent publishes when the table already contains stories, `related(story, existing)` calls `similarity(story, other)`. The `similarity` function calculates a weighted score using Python floating-point arithmetic and `round(...)`, returning a Python `float`. When `table.put_item(Item=item)` is executed with items containing float values in `similar[i]["score"]`, DynamoDB / `boto3` rejects them with:
```
TypeError: Float types are not supported. Use Decimal types instead.
```
This uncaught exception causes `handler()` to log the error and return HTTP 500.

## Fix
1. **Code Fix ([`src/app.py`](file:///private/tmp/h-UUEINj/src/app.py))**: Converted the float score in `similarity()` to a `Decimal` (`Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))`), which is natively supported and expected by `boto3` / DynamoDB.
2. **Regression Prevention ([`tests/test_publish.py`](file:///private/tmp/h-UUEINj/tests/test_publish.py))**: Added unit tests verifying that publishing to a non-empty table computes similarity scores and succeeds without raising `TypeError`, ensuring future changes cannot reintroduce this issue.
