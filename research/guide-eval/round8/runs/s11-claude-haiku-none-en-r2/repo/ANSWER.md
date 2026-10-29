# Second publish returns 500

## Cause

`similarity()` in `src/app.py` returned a Python `float` (`round(..., 4)`).
`related()` puts that value into each `similar` entry as `score`, and
`publish()` stores it with `table.put_item`. boto3's DynamoDB serializer
rejects Python floats:

    TypeError: Float types are not supported. Use Decimal types instead.

The first publish succeeds only because the table is empty, so `related()`
returns `[]` and no float is written. The second publish finds one existing
story, builds `similar: [{"slug": ..., "score": 0.xxxx}]`, and fails. The
`TypeError` is not a `ValueError`, so `handler()` maps it to a 500. The log
shows the same pattern: 201 for the first publish, then 500 for the next ones.

The existing test only publishes into an empty `FakeTable`, so it never reached
the float path and passed.

## Fix

- `src/app.py`: `similarity()` returns `Decimal(str(round(...)))`. `str()` of a
  rounded float gives the short form (e.g. `"0.3333"`), so the stored value is
  the same number as before. `Decimal` is imported from `decimal`.
- `tests/test_publish.py`: new `test_second_publish_stores_related_scores`. It
  publishes two stories through `handler()`, then checks for a 201, the expected
  `similar` slug, and that `score` is a `Decimal`. It fails on the old code with
  the 500 and passes with the fix.

## Why it won't come back

`tests/fake_dynamo.py` already rejects floats the way boto3 does, so any code
path that writes a float into an item now fails in the test suite. The new test
exercises that path (a non-empty `similar`), which the old test did not.

No data needs repair: the failed puts never stored anything. The first story
(`why-my-cron-ran-twice`, `similar=[]`) is valid as stored.
