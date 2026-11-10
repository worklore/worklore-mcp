# Second publish returns 500: float written to DynamoDB

## Cause

`publish()` stores each story with `similar: [{slug, score}]`. `score` comes from
`similarity()` in `src/app.py`, which ends in `round(..., 4)`. That is a Python
`float`.

- **First publish:** the table is empty, so `related()` has no candidates and
  returns `[]`. No float is ever built, and the write succeeds (201).
- **Second publish:** the table now holds one story. `related()` scores it, so
  `similar` contains a float. `table.put_item(Item=item)` then fails inside
  boto3's `TypeSerializer` with `TypeError: Float types are not supported`,
  which the `except Exception` in `handler()` turns into a 500.

The log matches this exactly: `logs/error.log` shows the 201 for
`why-my-cron-ran-twice`, then the `TypeError` and 500 on the next publish, with
the traceback ending in `table.put_item(Item=item)`, line 63.

The existing test only published into an empty `FakeTable`, so the scoring path
never ran. The fake table already rejects floats, so the test would have caught
the bug if it had seeded one story first.

## Fix

1. **`src/app.py`: convert floats at the write boundary.** A new `to_dynamo()`
   walks the item and turns every `float` into `Decimal(str(value))`, so
   `0.4286` is stored as `Decimal("0.4286")`. `publish()` now calls
   `table.put_item(Item=to_dynamo(item))`. Because the conversion covers the
   whole item, a float from any future path (division, averages, rounding)
   cannot reach `put_item`.

2. **`tests/test_publish.py`: exercise the populated-table path.**
   - `seeded_table()` seeds one story before the write-path tests.
   - `test_publish_into_populated_table_stores_scored_similar` checks that the
     scored `similar` entry is stored as a `Decimal`.
   - `test_second_publish_through_handler_returns_201` reproduces the production
     sequence through `handler()`.
   - `test_to_dynamo_converts_nested_floats_only` covers the converter.

Verification: `python3 -m unittest discover tests` passes 4/4 with the fix.
With `src/app.py` reverted to the original, the two populated-table tests fail
with the same `TypeError` as the log, and the converter test fails because it
does not exist yet.

## Colleague's note: what applied

- **Applied:** the diagnosis. The bug was on the scoring path that depends on
  existing rows, the empty-table test hid it, and the float came from a
  division/rounding step feeding an item dictionary.
- **Applied:** seeding one record before testing the write path. This is the
  test-side fix that would have caught the bug.
- **Not applied:** converting scores to integer percentages. It would have
  made the write succeed, but it changes what `score` means in stored data
  (`0.4286` becomes `43`) and loses precision for any reader that already
  expects a fraction. `Decimal` keeps the values the same.
- **Not applied:** "one-line change" as the whole fix. A one-line change to
  `similarity()` would fix this case only. The boundary conversion covers the
  other paths the note warns about.

## Caveat

Values read back from DynamoDB are `Decimal`, not `float`. `json.dumps()` cannot
serialize `Decimal` directly. This repo has no reader code, so nothing here
breaks. If the reader page serializes `similar[].score` with `json.dumps`, it
will need a `default=` hook or a `float()` conversion on read.

Nothing was deployed, published or sent to any external service.
