# Cause

`similarity()` returns a Python `float`. The first publish succeeds because its
`similar` list is empty, so no score is sent to DynamoDB. On the second publish,
`related()` adds a similarity score to that list, and boto3's DynamoDB
serializer rejects the float with `TypeError: Float types are not supported. Use
Decimal types instead.` The handler catches that exception and returns HTTP 500.

# Fix

`related()` now converts each score with `Decimal(str(...))` before it is placed
in the item written by `put_item()`. Using `str()` preserves the rounded decimal
score without importing the float's binary representation.

The regression test publishes two stories through `handler()`, requires both
responses to be HTTP 201, and checks that the second story's stored score is a
`Decimal`. The fake table applies the same float rejection as boto3, so removing
the conversion makes this test fail.

Verification: `python3 -m unittest discover tests` passes (2 tests). A
three-story handler scenario also returned 201 for every publish and stored only
`Decimal` similarity scores.
