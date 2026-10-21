# Cause

The first publish had no existing stories, so `similar` was empty and its DynamoDB item was valid. On the second publish, `similarity()` calculated a Python `float` for each existing story. `publish()` placed that float in `similar[].score`, and boto3 rejected the item during `put_item` with `TypeError: Float types are not supported. Use Decimal types instead.` The handler caught that exception and returned 500.

# Fix

`similarity()` now performs the weighted calculation with `Decimal` values and rounds the result to four decimal places as a `Decimal`. Every score stored in `similar` is therefore accepted by DynamoDB, including zero scores. A regression test publishes three stories through the handler and checks the stored score types and a calculated score. `python3 -m unittest discover tests -v` passes.
