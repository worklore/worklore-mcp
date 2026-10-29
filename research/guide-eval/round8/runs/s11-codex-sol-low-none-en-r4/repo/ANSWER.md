# Cause

The first publish has no existing stories, so `similar` is empty and the item saves. On the second publish, `related()` adds a similarity `score` returned by `similarity()` as a Python `float`. Boto3's DynamoDB serializer rejects floats, including ones nested in lists, causing `put_item` to raise `TypeError` and the handler to return 500.

# Fix

Convert each score to `Decimal` when building the stored `similar` entries, using the rounded score's string representation. DynamoDB accepts `Decimal`, and the existing four-decimal score precision is preserved. A regression test publishes three stories through the handler and checks that each publish succeeds and stored related scores are `Decimal` values.

Verified with `python3 -m unittest discover tests -v` (2 tests passed).
