# Cause

The second publish failed because `similarity()` in `src/app.py` returned a Python `float`: the divisions and weighted calculation produce floats, and `round(..., 4)` preserved that type. DynamoDB's boto3 serializer rejects floats, so `table.put_item(Item=item)` raised `TypeError: Float types are not supported. Use Decimal types instead.` The handler caught that exception and returned 500.

The first publish succeeded only because the table was empty. With no existing stories, `related()` returned an empty list and no similarity score was written. The second publish found the first story, added a float score to `similar`, and reached the failing serialization path.

# Fix

`similarity()` now returns an integer percentage from 0 to 100 by rounding the blended score multiplied by 100 without a decimal-places argument. Values stored in `similar[].score` are therefore integers accepted by DynamoDB.

`tests/test_publish.py` now covers the populated-table path: it publishes one story, publishes a matching second story, and verifies both the related-story result and the integer score type. This test reproduced the original `TypeError` before the fix and passes after it, preventing a regression to float scores.

Verification: `python3 -m unittest discover tests` passes both tests.

# Colleague's note

Applied parts:

- The explanation that DynamoDB rejects Python floats and that an empty first write hides state-dependent serialization bugs.
- Tracing the computed similarity score into the DynamoDB item.
- Converting scores to integer percentages at the storage boundary.
- Adding a regression test that seeds one record before testing the second write.

The note's real-AWS-table verification was not applicable here: the repository's `FakeTable` deliberately reproduces boto3's type validation, and verification remained local as required. The alternative of using `Decimal` was not needed because integer percentages provide the required DynamoDB-safe representation.
