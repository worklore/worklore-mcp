# Second publish failure

`logs/error.log` shows boto3 rejecting a Python float during `table.put_item`: `Float types are not supported. Use Decimal types instead.` The float came from `similarity()`, which calculates ratios and returns a rounded float. `related()` placed that score in the item's `similar` list. The first publish had no existing stories, so `similar` was empty and the invalid value was never written. Every later publish with an existing story entered the scoring path and returned 500.

`related()` now converts each score to `Decimal` before putting it in the item. `Decimal(str(score))` retains the existing four decimal place score calculation and produces a DynamoDB compatible number. A regression test publishes two stories through the handler using the DynamoDB validating fake table, then checks the second response, stored fractional score, and item count. `python3 -m unittest discover tests -v` passes (2 tests).

The colleague's note applies to the float rejection, the empty versus populated table behavior, and the need to test a seeded write path. Its integer percentage fix was not used because it would change the stored score scale and precision. No live DynamoDB publish was performed because this task is restricted to the current directory and forbids external publishing.
