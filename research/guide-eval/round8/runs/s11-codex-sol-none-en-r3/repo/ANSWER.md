# Second publish failure

The first publish stored no related stories, so its `similar` list was empty. On the second publish, `related()` added a score from `similarity()`. That function used Python float division and returned a float. DynamoDB's boto3 serializer rejects floats, which caused `put_item()` to raise `TypeError: Float types are not supported` and the handler to return 500.

`similarity()` now computes the weighted score with `Decimal` values and rounds it to four decimal places before storage. This preserves the score precision without putting a float in the DynamoDB item.

A regression test publishes two stories through the handler using the DynamoDB-validating fake table. It checks that both requests succeed and the second stored item contains a `Decimal` related-story score. `python3 -m unittest discover tests -v` passes (2 tests).
