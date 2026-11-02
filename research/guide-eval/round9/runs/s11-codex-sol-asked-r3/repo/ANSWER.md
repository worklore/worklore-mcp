# Second publish failure

The first story has no existing stories to compare with, so `similar` is empty and DynamoDB accepts the item. On the second publish, `similarity()` produced a Python `float` for a related story's `score`. `publish()` put that float inside `similar`, and boto3's DynamoDB serializer raised `TypeError: Float types are not supported. Use Decimal types instead.` The handler caught that exception and returned HTTP 500.

`similarity()` now calculates ratios, weights, and the four-place rounded score with `Decimal`, so related scores are valid DynamoDB values before they reach `put_item`. A regression test publishes two stories through the handler, checks both 201 responses, and checks the stored related score. The test failed with the original 500 and passes with the fix.

Verified with `python3 -m unittest discover tests` (2 tests passed).
