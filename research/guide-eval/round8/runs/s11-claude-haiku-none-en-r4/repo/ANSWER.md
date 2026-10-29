# Second publish returns 500: float stored in DynamoDB

## Cause

`publish()` stores each story's `similar` list, and every entry carries a `score`
produced by `similarity()`. That function returned a Python `float`
(`round(..., 4)`).

DynamoDB (via boto3) does not accept floats. It only accepts `Decimal`, `int`,
`str`, and similar types, so `put_item` raises
`TypeError: Float types are not supported. Use Decimal types instead.`

The first publish worked because the library was empty, so `similar` was `[]`
and no float was ever written. The second publish is the first one with an
existing story to score against, so it writes a float and fails. The log matches
this: the first publish is `similar=0 stored`, and every failure comes after it.

The existing test only publishes once, so it never reached a non-empty
`similar` list. The test fake (`tests/fake_dynamo.py`) does reject floats, so the
bug would have been caught if a second publish had been tested.

## Fix

- `src/app.py`: `similarity()` now returns `Decimal(str(round(score, 4)))`.
  The value is still rounded to 4 places, the ranking is unchanged, and
  `str()` avoids binary float artifacts when converting to `Decimal`.
- `tests/test_publish.py`: added `test_second_publish_stores_related_stories`,
  which publishes two stories and checks that the second one stores the first
  in `similar`. It fails on the old code with the same `TypeError` as production
  and passes with the fix.

## Keeping it from coming back

The regression test exercises the path that failed (a publish with a non-empty
library), and the fake table already rejects floats, so any future float in the
item will fail the test locally. Run with:

    python3 -m unittest discover tests
