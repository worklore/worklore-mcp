# Second publish returns 500

The first story has no existing stories to compare with, so its `similar` list is empty and `put_item` succeeds. On the second publish, `similarity()` used `/` and float weights to produce a Python `float` for `similar[0].score`. DynamoDB's boto3 serializer rejects floats (`TypeError: Float types are not supported. Use Decimal types instead.`), and `handler()` turns that exception into HTTP 500. This matches `logs/error.log`.

The score calculation now uses `Decimal` throughout and rounds to four decimal places before the value enters the stored item. A regression test sends two publish requests through `handler()` against the DynamoDB-validating fake table, checks that both return 201, and verifies the second item's related score is a `Decimal`. The test failed with 500 before the fix and passes afterward.

Verification: `python3 -m unittest discover tests -v` (2 tests passed).
