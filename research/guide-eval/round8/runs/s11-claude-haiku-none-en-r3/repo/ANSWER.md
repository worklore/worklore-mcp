# Second publish returns 500: float score in `similar`

## Cause

`similarity()` returns a Python float (`round(..., 4)`). `related()` put that
float into each `similar` entry as `score`, and `publish()` wrote the item to
DynamoDB with `put_item`. boto3's DynamoDB serializer rejects floats:

    TypeError: Float types are not supported. Use Decimal types instead.

The first publish works only because the library is empty at that point, so
`similar` is `[]` and no float is ever written. The second publish is the first
one with an existing story to compare against, so it writes a float and fails.
`handler()` catches the exception and returns 500. This matches
`logs/error.log`: the 201 at 09:14:02 is the first publish, and the 500s at
09:21:47 and 09:22:10 come after it.

The existing test published only once, so it never reached the failing path.
`tests/fake_dynamo.py` already rejects floats the way boto3 does, so the test
suite would have caught this if it had published twice.

## Fix

- `src/app.py`: `related()` stores the score as `Decimal(str(similarity(...)))`.
  Using `str()` keeps the rounded value (`0.4667`) instead of the float's
  binary representation. `from decimal import Decimal` is added.
- `tests/test_publish.py`: new `test_publish_second_story_with_related`
  publishes two stories and checks that the second one stores its related
  story. It fails on the original `app.py` (verified) and passes with the fix.

`python3 -m unittest discover tests` now runs two tests, both passing.

## Why it can't come back

The fake table rejects floats anywhere in an item, so any float that reaches
`put_item` now fails the test suite. The new test puts the second publish, the
first one with a non-empty `similar`, through that check. Any future change that
writes a float into the item fails the test before it reaches production.

Not changed: `publish()` still calls `table.scan()` without pagination. A table
larger than 1 MB would return partial results, so `similar` would be computed
from only part of the library. This is a separate issue and is not part of this
fix.
