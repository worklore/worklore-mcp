# Publishing failure

The first publish has no existing stories, so `similar` is empty. On the second publish, `related()` adds a similarity score as a Python `float` inside `similar`. DynamoDB's boto3 serializer rejects floats, including nested values, so `put_item()` raises `TypeError: Float types are not supported` and the handler returns 500.

`related()` now converts each rounded score to `Decimal` via its string representation before building the item. This keeps the score's four-decimal precision and gives DynamoDB a supported numeric type. A regression test publishes three stories through the handler using the DynamoDB-validating fake table and checks that every stored related score is a `Decimal`.

Verified with `python3 -m unittest discover tests` (2 tests pass).
