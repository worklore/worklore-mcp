# Cause and fix

The first publish has no existing stories, so its `similar` list is empty and DynamoDB accepts the item. On the second publish, `related()` adds a similarity score produced as a Python `float`. Boto3's DynamoDB serializer rejects floats (`TypeError: Float types are not supported`), and the handler returns 500.

`related()` now converts each rounded score to `Decimal` before it enters the stored item. `Decimal(str(score))` preserves the rounded decimal value and is accepted by DynamoDB. A regression test publishes two stories through the handler, checks both responses are 201, and verifies the second item's related score is a `Decimal`. `python3 -m unittest discover tests` passes (2 tests).
