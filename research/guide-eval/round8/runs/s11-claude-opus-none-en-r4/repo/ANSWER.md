# Why the second publish returns 500

## Cause

`publish()` stores each story with its `similar` list: `[{slug, score}]`.
`similarity()` returns a Python **float** (`round(0.7 * tag_score + 0.3 * word_score, 4)`).
boto3's DynamoDB serializer doesn't accept floats. It raises
`TypeError: Float types are not supported. Use Decimal types instead.`
(`logs/error.log`, from `table.put_item` at `src/app.py:63`). `handler()` catches that
as a generic exception and returns 500.

The **first** publish works only because the table is empty: `similar` is `[]`, so
the item has no floats at all (log: `similar=0 stored`). From the second publish on,
there's always at least one existing story, so a float score ends up in the item and
every publish fails. The old test published just one story, so it never hit this case.

## Fix

- `src/app.py`: a new `to_dynamo()` walks the whole item and turns every float into
  `Decimal(str(x))`. Going through `str` stores `0.7` as `0.7`, not its binary
  expansion. It raises `ValueError` (400) for NaN or infinity, which DynamoDB can't
  store. `publish()` calls it on the item right before `put_item`.
  - Why this stops it coming back: the conversion happens at the storage boundary
    and covers the whole item. Any float field added later is converted too, not
    just `score`.
- `tests/test_publish.py`: three regression tests:
  - two publishes in a row through `handler()`: both return 201 and the stored score
    is a `Decimal`
  - six publishes, checking that `similar` is capped at 3
  - a unit test for `to_dynamo` (nested floats, bools kept as bools, NaN rejected)

  These tests fail on the old code (2 failures, 1 error) and pass with the fix:
  `python3 -m unittest discover tests` gives 4 tests, OK.
