# Second publish failure

The first publish stores an empty `similar` list. On the second publish, `related()` adds a similarity score, but `similarity()` produced a Python `float`. The DynamoDB boto3 resource rejects floats during `put_item`, raising `TypeError: Float types are not supported. Use Decimal types instead.` The handler catches that error and returns 500.

`similarity()` now calculates and rounds scores using `Decimal` throughout, so every stored score is a DynamoDB-compatible number. A regression test publishes two stories through the same table, checks that the second request succeeds, and verifies its stored score is a `Decimal`.

Verified with `python3 -m unittest discover tests` (2 tests pass).
