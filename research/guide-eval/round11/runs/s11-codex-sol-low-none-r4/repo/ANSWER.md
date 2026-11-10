# Second publish failure

The first publish stored `similar: []` because the table had no other stories. On the second publish, `related()` added a similarity score produced as a Python `float`. The `put_item` call then failed while boto3 serialized that nested value: DynamoDB's boto3 serializer rejects floats (`TypeError: Float types are not supported. Use Decimal types instead.`). The handler caught the error and returned 500.

`related()` now converts each calculated score to `Decimal` using its string representation before it becomes part of the item sent to DynamoDB. This keeps the existing score calculation and ordering while ensuring stored scores use a type boto3 accepts. A regression test publishes two stories through the handler, checks that both requests return 201, and verifies the second item's stored score is a `Decimal`. The in-memory table rejects floats like boto3, so this test would fail with the original code.

Verified with `python3 -m unittest discover tests` (2 tests passed) and `git diff --check`.
