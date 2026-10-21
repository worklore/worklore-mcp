# Why the second publish returns 500

## Cause

`publish()` stores each story with its three most similar existing stories,
`similar: [{slug, score}]`. `similarity()` returns `round(0.7 * tag_score + 0.3 * word_score, 4)`,
which is a Python `float`. boto3's DynamoDB serializer rejects floats:

```
TypeError: Float types are not supported. Use Decimal types instead.
```

(`logs/error.log`, raised from `table.put_item(Item=item)` in `src/app.py`.)

The first publish worked only because the table was empty. `related()` had
nothing to score, so `similar` was `[]` and the item had no floats in it
(`similar=0` in the log). From the second publish on there is always at least
one existing story, so a float score ends up in the item and `put_item` throws.
The generic `except Exception` in `handler()` turns that into a 500.

The existing test didn't catch it because it only published into an empty table.

## Fix

- `src/app.py`: added `to_dynamo()`, which goes through the item recursively and
  replaces every `float` with `Decimal(str(value))`. `publish()` calls it on the
  whole item right before `put_item`. Because it covers the whole item at the
  write boundary, it doesn't matter which field a float is in. So a new computed
  field added later (an average, a ratio, a weight) can't cause this error again.
  Scores are stored as exact DynamoDB numbers such as `0.4123`.
- `tests/test_publish.py`: added a regression test that adds one story first and
  then publishes a second one through `handler()`. It checks that the response
  is 201 and that the stored score is a non-zero `Decimal`. Also added a unit
  test for `to_dynamo()` with nested floats. Both new tests fail on the old code
  and pass with the fix (`python3 -m unittest discover tests`: 3 tests, OK).

When adding write-path tests in future, start from a table that already has
data. The empty-table path only runs once in production.
