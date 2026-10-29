# Issue Analysis and Resolution

## Cause of the Bug
When the first story is published, the DynamoDB table is empty (`existing = []`), so `related(story, existing)` returns an empty list `[]`. No similarity scores are calculated, and the item is stored successfully with `similar: []`.

When a second story is published, existing stories are present in the table. The `related()` function calculates similarity scores via `similarity(story, other)`, which returned a Python `float` (`round(0.7 * tag_score + 0.3 * word_score, 4)`).

Because `boto3`'s DynamoDB serializer (`TypeSerializer`) explicitly disallows Python `float` types and requires `decimal.Decimal` to avoid binary floating-point precision loss, attempting `table.put_item(Item=item)` raises:
```
TypeError: Float types are not supported. Use Decimal types instead.
```
This uncaught `TypeError` gets caught by the general `except Exception:` clause in `handler()`, logging the error and returning HTTP `500`.

## Fix
In [`src/app.py`](src/app.py):
1. Imported `Decimal` from the Python standard library `decimal` module.
2. Updated `similarity()` to return `Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))` instead of a raw Python `float`.
3. Added unit tests in [`tests/test_publish.py`](tests/test_publish.py) covering publishing subsequent stories with similarity scores and invoking `handler()` multiple times.
