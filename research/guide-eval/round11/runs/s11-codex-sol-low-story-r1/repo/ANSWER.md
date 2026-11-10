# Second publish failure

`logs/error.log` shows boto3 rejecting a Python float during `put_item`: `Float types are not supported. Use Decimal types instead.` The first publish scans an empty table, so `similar` is empty. On the second publish, `related()` computes a similarity score, puts that float inside `similar`, and DynamoDB serialization raises `TypeError`. The handler returns 500.

`related()` now converts each computed score to `Decimal` before it enters the item written to DynamoDB. `Decimal(str(score))` preserves the existing rounded score value without changing the score scale. A regression test publishes two stories through the handler, checks both responses are 201, and checks the second stored item has a fractional `Decimal` score. `python3 -m unittest discover tests -v` passes (2 tests).

The colleague's note applied to the empty-table versus populated-table path, boto3's rejection of floats, conversion at the write boundary, and testing a seeded write. Its integer-percentage fix did not apply because it would change this service's score representation. No real DynamoDB publish was performed; verification used the repository's validating in-memory table.
