# Cause

`similarity()` calculated each related-story score with Python floating-point arithmetic and returned a `float`. The first publish had no existing stories, so its `similar` list was empty and DynamoDB accepted the item. The second publish added a non-empty `similar` entry containing a float score. DynamoDB's boto3 serializer does not support floats and raised `TypeError: Float types are not supported. Use Decimal types instead.`, which `handler()` converted to the logged 500 response.

# Fix

`src/app.py` now performs similarity arithmetic with `decimal.Decimal` and quantizes scores to four decimal places, preserving the previous precision while producing values DynamoDB accepts. Sorting and score semantics are unchanged.

`tests/test_publish.py` now exercises two sequential publishes through `handler()`. It verifies that both return 201, both stories are stored, and the second story's related score is stored as `Decimal("1.0000")`. The fake table applies the same float rejection as boto3, so reintroducing float scores makes this regression test fail.

Verification: `python3 -m unittest discover tests` — 2 tests passed.
