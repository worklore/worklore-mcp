# Second publish failure

`publish()` stores related stories in the `similar` list. On the first publish, the table is empty, so the list contains no scores and the write succeeds. On the second publish, `similarity()` produces a Python `float` score. DynamoDB's boto3 serializer rejects floats, causing `put_item()` to raise `TypeError` and the handler to return 500. The error in `logs/error.log` is this serializer failure.

The score calculation now uses `Decimal` for ratios, weights, and four-place rounding. Every generated score is therefore a DynamoDB-compatible `Decimal` before it reaches `put_item()`. A regression test publishes three related stories through the handler and checks that all publishes return 201 and stored scores are `Decimal` values.
