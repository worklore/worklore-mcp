# Root Cause and Fix: Publishing 500 Error

## Cause
When the first story is published to an empty DynamoDB table, `table.scan()` returns no items (`existing = []`). Consequently, `similar` is an empty list `[]` and `table.put_item()` succeeds.

When the second story is published, existing stories are found in the table. The `related()` function calculates a similarity score for each existing story using `similarity()`, which returned a Python `float` rounded to 4 decimal places. The resulting item placed into DynamoDB contained:
```python
"similar": [{"slug": ..., "score": 0.xxxx}]
```
Boto3's `TypeSerializer` does not support Python `float` values when serializing DynamoDB attributes and raises `TypeError: Float types are not supported. Use Decimal types instead.` This uncaught exception in `publish()` caused `handler()` to log the error and return HTTP 500.

## Fix
In [`src/app.py`](src/app.py):
1. Imported `Decimal` from the Python standard library module `decimal`.
2. Updated `similarity(a, b)` to return `Decimal(str(round(0.7 * tag_score + 0.3 * word_score, 4)))` instead of a Python `float`.

In [`tests/test_publish.py`](tests/test_publish.py):
- Added a regression test `test_publish_second_story_succeeds_with_similarity` that publishes two stories sequentially against `FakeTable`, ensuring subsequent publications calculate similarity scores as `Decimal` and persist without `TypeError`.
