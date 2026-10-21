# Root Cause and Fix for Publish 500 Error

## Cause
When publishing the very first story into an empty table, `existing` stories returned by `table.scan(...)` is empty, so `related(story, existing)` produces an empty list (`similar: []`). Thus, no similarity scores are stored.

When publishing a second story, `existing` contains the first story. The `similarity()` function computes a similarity metric using floating-point arithmetic and returns a Python `float` (`round(...)`). This float is stored in the `similar` list under the `score` field (e.g. `similar: [{'slug': ..., 'score': 0.1234}]`).

DynamoDB (via `boto3` / `botocore`'s `TypeSerializer`) does not support Python `float` types and strictly requires numeric values to be represented as `decimal.Decimal` objects. When `table.put_item(Item=item)` is executed on the second publish, boto3 raises:
```
TypeError: Float types are not supported. Use Decimal types instead.
```
In `handler()`, this unhandled `TypeError` is caught by the generic `except Exception:` block and logged as `publish failed`, returning HTTP status `500`.

## Fix
1. In [`src/app.py`](file:///tmp/h-y2cuaq/src/app.py), imported `Decimal` from the standard `decimal` module.
2. In `similarity(a, b)`, converted the calculated float score to `Decimal(str(round(...)))`.
3. Added unit tests in [`tests/test_publish.py`](file:///tmp/h-y2cuaq/tests/test_publish.py) covering multiple consecutive publishes and the handler response to verify that `similar` items serialize cleanly without raising `TypeError`.
