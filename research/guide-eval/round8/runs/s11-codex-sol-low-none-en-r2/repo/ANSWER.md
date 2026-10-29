# Cause

The first publish had no existing stories, so `similar` was empty and the DynamoDB write succeeded. On the second publish, `related()` added a `score` produced by `similarity()` as a Python `float`. Boto3's DynamoDB serializer rejects floats, including `0.0`, so `put_item` raised `TypeError` and the handler returned 500.

# Fix

`related()` now converts each rounded score to `Decimal` using its string representation before adding it to the stored item. This preserves the intended four-decimal score while giving DynamoDB a supported numeric type. A regression test publishes three stories through the handler and checks that related scores, including zero, are `Decimal` values. `python3 -m unittest discover tests` passes.
