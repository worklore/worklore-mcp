# Second publish failure

The first publish stores an empty `similar` list. On the second publish, `related()` adds a similarity score produced as a Python `float`. DynamoDB's boto3 serializer rejects floats, including values nested inside a list or map, so `put_item()` raises `TypeError` and the handler returns 500.

`related()` now converts each rounded score to `Decimal` before it enters the item sent to DynamoDB. This keeps the existing score calculation and four decimal place rounding while using a type DynamoDB accepts. A regression test publishes two stories through the handler and verifies that the second request succeeds and its stored related score is a `Decimal`.
