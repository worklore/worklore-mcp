# Second publish failure

The first story had no existing stories to compare, so its `similar` list was empty and DynamoDB accepted the item. On the second publish, `related()` added a similarity score produced by `similarity()` as a Python `float`. Boto3's DynamoDB serializer rejects floats, causing the `TypeError` in `logs/error.log`; the handler turned it into HTTP 500.

`related()` now converts each score to `Decimal` using its string representation before adding it to the item. This preserves the rounded score and gives DynamoDB a supported numeric type. A regression test publishes two stories through the handler and checks that both requests succeed and the second item's score is a `Decimal`.

Verified with `python3 -m unittest discover tests` (2 tests passing).
