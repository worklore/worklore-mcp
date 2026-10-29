# Second publish failure

The first publish has no existing stories, so its `similar` list is empty. On the second publish, `related()` adds a score from `similarity()`. That score is a Python `float`, and boto3's DynamoDB Table resource rejects floats when serializing the item (`TypeError: Float types are not supported. Use Decimal types instead.`). The exception reached the handler's generic error path, producing the 500 in `logs/error.log`.

`publish()` now converts all nested floats in the item to `Decimal` immediately before `put_item`. This covers similarity scores and any future numeric fields added to the item. It rejects non-finite floats, which DynamoDB cannot store. A regression test publishes three stories through the handler, checks that each request returns 201, and checks that stored similarity scores are `Decimal` values.

Verification: `python3 -m unittest discover tests` passes (2 tests).
