# Second publish failure

`logs/error.log` shows boto3 rejecting a Python float during `table.put_item`: `Float types are not supported. Use Decimal types instead.` The float came from `similarity()`, which divides tag and word counts and returns a rounded float. `related()` placed that score inside the item's `similar` list. The first publish succeeded because the table was empty, so `similar` was empty and no float reached DynamoDB. Every later publish with an existing story followed the scoring path and failed.

The fix converts each computed score to `Decimal` before adding it to the DynamoDB item. It preserves the existing four-decimal score while using a type boto3 can serialize. A regression test publishes two stories through the handler using the DynamoDB-validating fake table, then checks the second stored item's related score. Run it with `python3 -m unittest discover tests`.

The colleague's note applied to the empty-table versus populated-table behavior, DynamoDB's rejection of floats, and the need for a seeded write-path test. Its integer-percentage fix was not used because it would reduce the precision of the existing four-decimal scores; `Decimal` keeps that precision.
