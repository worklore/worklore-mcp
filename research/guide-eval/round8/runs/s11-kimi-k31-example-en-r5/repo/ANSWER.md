# Cause

DynamoDB rejects Python `float` values. `similarity()` returns a float, and `related()` placed that value directly in each `similar[].score` field passed to `put_item()`.

The first publish succeeded because the table was empty: `related()` returned an empty list, so no score was calculated or serialized. The second publish found the first story, calculated a float score, and failed in DynamoDB serialization with `TypeError: Float types are not supported. Use Decimal types instead.` The handler converted that exception into the observed 500 response.

# Fix

In `src/app.py`, `related()` now converts each similarity ratio to an integer percentage before adding it to the DynamoDB item:

```python
int(round(similarity(story, other) * 100))
```

DynamoDB accepts Python integers, so no float reaches the write.

A regression test in `tests/test_publish.py` now publishes twice through `handler()`. It verifies that both responses are 201 and that the second story's related score is the integer `100`. This exercises the populated-table path that the original empty-table-only test missed and will fail if a float is written there again.

Verification: `python3 -m unittest discover tests` passes both tests. The tests use the existing in-memory table with boto3-compatible type validation; no real AWS table was used.

# Colleague's note

Applied: the DynamoDB float diagnosis, the explanation of why an empty first write hides the bug, conversion to integer percentages at the item-building boundary, and a regression test that seeds existing data by publishing once before testing the second write.

Not applied: the alternative of using `Decimal` was unnecessary because integer percentages fit this service. No real-table publish or deployment was performed; verification stayed within the repository's existing test setup.
