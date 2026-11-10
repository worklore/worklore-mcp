# Second publish failure

The first publish finds no existing stories, so `related()` produces an empty list. On the second publish, `similarity()` calculates a Python float and places it in `similar[0].score`. `publish()` passes that nested float to `table.put_item()`. Boto3's DynamoDB serializer rejects floats, producing the `TypeError: Float types are not supported` shown in `logs/error.log`; the handler converts that exception into HTTP 500.

The fix converts each rounded similarity score to `Decimal` before it enters the DynamoDB item. This retains the existing score scale and four-decimal rounding while using a type DynamoDB accepts. A regression test publishes two stories through the handler to the same validating fake table, checks that both requests return 201, and checks that the second item contains a `Decimal` related score. `python3 -m unittest discover tests -v` passes.

The colleague's note applied to the empty-table versus populated-table path, the float restriction in DynamoDB, converting computed scores at the write boundary, and testing a seeded table with a second write. Its integer-percentage fix was not used because it would change the stored score scale. Its suggestion to publish against a real table was not used because this task is limited to local work and the fake table validates DynamoDB-compatible types.
