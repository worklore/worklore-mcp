# Second publish failure

`logs/error.log` shows the first publish returning 201 with `similar=0`. On the next publish, `publish()` finds the first story and puts a similarity score in `similar`. `similarity()` calculated that score with Python float division and float weights. DynamoDB's boto3 serializer rejects floats, so `table.put_item(Item=item)` raised `TypeError: Float types are not supported. Use Decimal types instead.` The handler caught it and returned 500. The first publish succeeded only because its empty `similar` list contained no score.

The fix calculates both overlap ratios and their weighted score with `decimal.Decimal`, then rounds the result to the existing four decimal places. The item sent to DynamoDB therefore contains a supported numeric type while retaining the score's precision. A regression test publishes two stories through the handler into the validating in-memory table, checks that both requests return 201, and checks that the second stored story has a nonzero `Decimal` related score. `python3 -m unittest discover tests -v` passes (2 tests).

## Colleague's note

The empty-table versus populated-table path, DynamoDB's rejection of Python floats, and a test that writes after seeding a story all apply here. Converting scores to integer percentages was specific to that case; this service keeps four decimal places, so it now uses `Decimal` instead. The proposed real-table verification was not run because this task is restricted to the current directory and prohibits external services; the local fake table validates the same float rejection.
