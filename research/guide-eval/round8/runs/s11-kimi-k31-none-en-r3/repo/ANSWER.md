# Cause

The first publish succeeds because its `similar` list is empty. The second publish finds the first story, and `similarity()` returns its score as a Python `float`. That float is placed in `similar[*].score` and passed to DynamoDB. DynamoDB's boto3 serializer rejects floats with `TypeError: Float types are not supported. Use Decimal types instead.`, which the handler turns into a 500 response.

# Fix

`related()` now converts each rounded similarity score to `Decimal` via `Decimal(str(...))` before adding it to the item. This uses DynamoDB's supported numeric type without exposing a float's binary representation. Sorting and the calculated score values are unchanged.

A regression test publishes two stories through `handler()`, requires both responses to be 201, and verifies that the second story's stored related score is a `Decimal`. The test uses the same DynamoDB type validation that reproduced the original failure, so reintroducing a float in the stored item will fail the test.
