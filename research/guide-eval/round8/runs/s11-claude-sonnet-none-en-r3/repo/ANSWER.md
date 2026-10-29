# Why the second publish returns 500

**Cause.** `publish()` stores `similar: [{slug, score}]`, and `score` comes from `similarity()`, which returns a Python `float` (`round(..., 4)`). boto3's DynamoDB serializer rejects floats (`TypeError: Float types are not supported. Use Decimal types instead.`). The first publish succeeds only because the library is empty, so `similar` is `[]` and no float is ever written. From the second publish on, `similar` contains scores and `put_item` fails. `handler()` turns the exception into a 500.

**Fix.** `src/app.py` now passes the item through `to_dynamo()`, which recursively converts floats to `Decimal(str(x))`, before `put_item`. Converting at the storage boundary means any float added to the item later is also handled. `tests/test_publish.py` has a new regression test that publishes two stories in a row. It fails without the fix, because the fake table validates items the way boto3 does.

**Notes (not changed).** `publish()` reads existing stories with a single `scan`, which stops at 1 MB. Once the library is large, the related list will only consider the first page of results.
