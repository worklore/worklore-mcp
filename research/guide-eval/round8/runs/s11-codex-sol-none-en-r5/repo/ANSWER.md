# Second publish failure

The first publish had no existing stories, so its `similar` list was empty. On the second publish, `similarity()` produced a Python `float` for `similar[].score`. DynamoDB's boto3 serializer rejects floats (`Float types are not supported. Use Decimal types instead.`), so `put_item()` raised and the handler returned 500. The exception in `logs/error.log` identifies this serialization failure.

The fix calculates and rounds similarity scores with `decimal.Decimal` throughout. Every score stored in `similar` is now a DynamoDB-supported `Decimal`, including zero scores. A regression test publishes three stories through the handler and checks the stored scores and successful responses, so the second-publish failure is covered.

Verified with `python3 -m unittest discover tests -v` (2 tests pass) and `git diff --check`.
