# Why the second publish failed

`publish()` stores similarity scores inside the new story's `similar` list. On the first publish, the table is empty, so that list contains no scores. On the second publish, `similarity()` returns a Python `float`; `related()` put it directly into the DynamoDB item. Boto3 rejects floats, including nested values, causing the `TypeError: Float types are not supported. Use Decimal types instead.` in `logs/error.log` and the HTTP 500.

# Fix and regression protection

`related()` now converts each score to `Decimal` before adding it to the item. The conversion uses `Decimal(str(score))`, preserving the existing rounded 0–1 score values without introducing a binary float approximation into DynamoDB. A regression test publishes two stories through the handler into the validating fake table, checks that both return 201, and verifies that the second stored item has a `Decimal` related score. This exercises the populated-table path that the original first-publish test missed.

Verified with `python3 -m unittest discover tests -v` (2 tests passed). No external publish was performed.
