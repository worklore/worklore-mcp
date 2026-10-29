# Cause and fix

The first publish has no existing stories, so its `similar` list is empty and DynamoDB accepts the item. On the second publish, `similarity()` produces a Python `float` for a related story. `related()` placed that float in `similar[].score`, and boto3's DynamoDB serializer rejected the item with `TypeError: Float types are not supported. Use Decimal types instead.` The handler caught the error and returned 500.

`related()` now converts each rounded similarity score to `Decimal` before it becomes part of the stored item. Using `Decimal(str(score))` preserves the calculated decimal value without carrying over binary float representation artifacts. A regression test publishes three stories through the handler, checks each returns 201, and verifies stored related scores are `Decimal` values.
