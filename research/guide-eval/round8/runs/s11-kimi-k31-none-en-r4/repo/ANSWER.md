# Cause

`similarity()` returns a Python `float`. On the first publish there are no existing stories, so `similar` is empty and no score is sent to DynamoDB. On the second publish, `related()` adds a float score to `similar`; boto3 rejects floats with `TypeError: Float types are not supported. Use Decimal types instead.` The handler catches that exception and returns HTTP 500.

# Fix

`related()` now converts each score with `Decimal(str(score))` before putting the item in DynamoDB. This preserves the displayed rounded value without binary-float artifacts and uses the numeric type DynamoDB accepts.

A regression test publishes two stories through `handler()`, verifies that both return 201, and checks that the second story's stored similarity score is a `Decimal`.

# Verification

`python3 -m unittest discover tests` — 2 tests passed.
