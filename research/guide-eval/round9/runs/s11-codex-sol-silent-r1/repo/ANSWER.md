# Second publish failure

The first publish has no existing stories, so it stores `similar: []` and succeeds. On the second publish, `related()` adds a score from `similarity()`. That function used Python float division, so `table.put_item()` received a float in `similar[0].score`. Boto3's DynamoDB serializer rejects floats (`Float types are not supported. Use Decimal types instead.`), causing the 500 in `logs/error.log`.

`similarity()` now calculates and rounds the score with `Decimal` throughout, so every stored score is a DynamoDB-compatible number. A regression test publishes three stories through the handler using the DynamoDB-validating fake table; it checks that each request succeeds and that the stored similarity scores are `Decimal` values, including a nonzero score on the second publish.

Verified with `python3 -m unittest discover tests -v` (2 tests passing).
