# Cause

`similarity()` returns a Python `float`. The first publish has no existing stories, so its `similar` list is empty and DynamoDB accepts the item. On the second publish, `related()` adds a similarity entry containing a float `score`. DynamoDB's serializer rejects floats with `TypeError: Float types are not supported. Use Decimal types instead.`; `handler()` catches that exception and returns HTTP 500.

# Fix

`related()` in `src/app.py` now converts each computed score with `Decimal(str(score))` before putting it in the DynamoDB item. Converting through the rounded score's string representation preserves its decimal value without exposing DynamoDB to binary floating-point details.

A regression test in `tests/test_publish.py` sends two consecutive publish requests through `handler()`, verifies that both return 201, and checks that the second story is stored with a `Decimal` similarity score. This test reproduced the original 500 before the fix and passes afterward.

Verification: `python3 -m unittest discover tests` (2 tests passed).
