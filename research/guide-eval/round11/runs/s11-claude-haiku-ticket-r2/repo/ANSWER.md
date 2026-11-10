# Second publish returns 500: float scores reach DynamoDB

## Cause

`similarity()` in `src/app.py` returns a Python `float` (`round(..., 4)`), and
`related()` stores it as `similar[].score`. The item is written with
`table.put_item(Item=item)`. boto3 does not accept Python floats, so the write
raises `TypeError: Float types are not supported. Use Decimal types instead.`

The bug only runs when there is an existing story to score against.

- Publish #1: the table is empty, `existing` is `[]`, `similar` is `[]`, and no
  float is ever built. It returns 201.
- Publish #2: `existing` has one item, `related()` computes a score, the float
  goes into the item, and the write fails. It returns 500.

The existing test only published into an empty `FakeTable`, so it never reached
the scoring path. `tests/fake_dynamo.py` already rejects floats the way boto3
does, so the bug was reproducible in the test suite. The test just never seeded
the table.

## Fix

1. **One write-point conversion.** `to_dynamo()` in `src/app.py` walks the item
   recursively and converts every `float` to `Decimal(str(x))`. `publish()` calls
   it right before `put_item`. Every path that can produce a float (scores, ratios,
   averages, anything added later) is covered, not only the one that failed.
   `Decimal(str(x))` keeps the value as written (`0.4` stays `0.4`).
2. **Tests that exercise the populated table.** `tests/test_publish.py` now:
   - publishes a second story through `handler()`, the same entry point production
     uses, and expects 201;
   - checks that stored `similar[].score` values are `Decimal`;
   - publishes five stories in sequence;
   - unit-tests `to_dynamo()` with nested floats.

   Against the original `app.py`, the populated-table tests fail (2 failures,
   2 errors). Against the fixed code, all 6 pass.

Run the tests with `python3 -m unittest discover tests` from the repo root.

## Colleague's note: what applied and what didn't

**Applied**
- The cause: a float reaches `put_item` only once the table has data, so the
  empty-table path hides it.
- The lesson: seed the table in write-path tests so the populated path runs. The
  new tests do this, and `test_second_publish_on_populated_table_returns_201`
  is the regression test.
- Scoring, averages and rounded values feeding item dictionaries are where floats
  come from. `to_dynamo()` covers all of them at the write point.

**Not applied**
- **Integer percentages.** The colleague turned scores into integer percentages.
  I used `Decimal` instead. Integer percentages would drop the 4-decimal precision
  of the score, so close matches could tie and the top-3 order could change.
  `Decimal` also works with DynamoDB and keeps the stored score unchanged.
- **"One-line change."** A one-line change would fix this one float. The
  write-point conversion is slightly larger, but it means the next float added to
  an item cannot break publishing again.

## Not done

- Nothing was deployed, published, or sent to any external service.
- The changes are uncommitted in the working tree. `logs/error.log` is unchanged.
- The tests use the in-memory `FakeTable`, not real DynamoDB. The fake's float
  check matches the production error message, but this has not been run against
  AWS.
