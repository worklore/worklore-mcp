# Second publish failure

The first publish has no existing stories, so `similar` is empty and DynamoDB accepts the item. On the second publish, `related()` adds a similarity score. `similarity()` produced a Python `float`, and boto3's DynamoDB serializer rejects floats (`TypeError: Float types are not supported. Use Decimal types instead.`). The handler caught that exception and returned HTTP 500.

`similarity()` now computes and rounds scores using `Decimal`, so every generated `similar[].score` is a DynamoDB-supported number. A regression test publishes two stories through the handler and checks that the second item stores a `Decimal` score. `python3 -m unittest discover tests` passes (2 tests).
